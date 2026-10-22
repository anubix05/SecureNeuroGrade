"""
SecureNeuroGrade — Authentication Module
========================================
Password hashing, verification, and login/logout helpers.
Uses bcrypt for password hashing (per AGENTS.md §11).

NEVER stores plaintext passwords.
"""

import logging

from flask import request
from flask_login import login_user, logout_user

from app import bcrypt, db
from app.models.database_models import User, AuditEventType
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)


def hash_password(plaintext_password):
    """
    Hash a plaintext password using bcrypt.

    Args:
        plaintext_password: The raw password string.

    Returns:
        Bcrypt hash string suitable for database storage.
    """
    return bcrypt.generate_password_hash(plaintext_password).decode('utf-8')


def verify_password(stored_hash, plaintext_password):
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        stored_hash: The bcrypt hash from the database.
        plaintext_password: The raw password to check.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.check_password_hash(stored_hash, plaintext_password)


def authenticate_user(username, password):
    """
    Authenticate a user by username and password.

    Args:
        username: The username to look up.
        password: The plaintext password to verify.

    Returns:
        The User object if authentication succeeds, None otherwise.
    """
    user = User.query.filter_by(username=username).first()

    if user is None:
        logger.warning('Login attempt for non-existent user: %s', username)
        log_audit_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            details=f'Unknown username: {username}',
            ip_address=request.remote_addr,
            success=False,
        )
        return None

    if not user.is_active:
        logger.warning('Login attempt for deactivated user: %s', username)
        log_audit_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            user_id=user.id,
            details='Account is deactivated',
            ip_address=request.remote_addr,
            success=False,
        )
        return None

    if not verify_password(user.password_hash, password):
        logger.warning('Failed password for user: %s', username)
        log_audit_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            user_id=user.id,
            details='Invalid password',
            ip_address=request.remote_addr,
            success=False,
        )
        return None

    return user


def perform_login(user):
    """
    Log a user into the Flask session.

    Args:
        user: The authenticated User object.

    Returns:
        True if login succeeded.
    """
    login_user(user, remember=False)
    logger.info('User logged in: %s (%s)', user.username, user.role)
    log_audit_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id=user.id,
        details=f'Role: {user.role}',
        ip_address=request.remote_addr,
    )
    return True


def perform_logout(user):
    """
    Log a user out of the Flask session.

    Args:
        user: The current User object (from current_user).
    """
    if user and user.is_authenticated:
        log_audit_event(
            event_type=AuditEventType.LOGOUT,
            user_id=user.id,
            ip_address=request.remote_addr,
        )
        logger.info('User logged out: %s', user.username)
    logout_user()
