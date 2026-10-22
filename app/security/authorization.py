"""
SecureNeuroGrade — Authorization Module
=======================================
Role-based access control decorators and helpers.

Access is enforced on the server (per AGENTS.md §10).
Do not rely solely on hiding frontend buttons.

Roles:
    - LAB_TECHNICIAN: Upload scans, view upload status
    - DOCTOR: View results, access patient records
"""

import logging
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

from app.models.database_models import AuditEventType
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)


def role_required(*roles):
    """
    Decorator to restrict route access to specific user roles.
    Server-side enforcement — returns 403 Forbidden for unauthorized roles.

    Usage:
        @role_required('DOCTOR')
        def doctor_dashboard():
            ...

        @role_required('LAB_TECHNICIAN', 'DOCTOR')
        def shared_view():
            ...

    Args:
        *roles: One or more role strings (e.g., 'DOCTOR', 'LAB_TECHNICIAN').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                logger.warning(
                    'Access denied: user %s (role=%s) tried to access '
                    'resource requiring roles %s',
                    current_user.username, current_user.role, roles
                )
                log_audit_event(
                    event_type=AuditEventType.ACCESS_DENIED,
                    user_id=current_user.id,
                    details=(
                        f'Required roles: {roles}, '
                        f'user role: {current_user.role}'
                    ),
                )
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def is_authorized(user, required_role):
    """
    Check if a user has a specific role.

    Args:
        user: The User object to check.
        required_role: The role string to verify.

    Returns:
        True if the user has the required role, False otherwise.
    """
    if user is None or not user.is_authenticated:
        return False
    return user.role == required_role
