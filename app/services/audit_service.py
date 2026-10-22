"""
SecureNeuroGrade — Audit Service (Module M4)
============================================
Logs security- and workflow-relevant events to the AuditLog table.

Event types (per AGENTS.md §17):
    LOGIN_SUCCESS, LOGIN_FAILURE, LOGOUT,
    SCAN_UPLOADED, SCAN_REJECTED, SCAN_ACCEPTED,
    INFERENCE_STARTED, INFERENCE_COMPLETED, INFERENCE_FAILED,
    RESULT_VIEWED, ACCESS_DENIED

Never logs: passwords, encryption keys, session secrets,
full medical images, unnecessary patient-identifying information.
"""

import logging

from app import db
from app.models.database_models import AuditLog

logger = logging.getLogger(__name__)


def log_audit_event(
    event_type,
    user_id=None,
    scan_id=None,
    model_version=None,
    details=None,
    ip_address=None,
    success=True,
):
    """
    Create an audit log entry.

    Args:
        event_type: One of AuditEventType constants.
        user_id: ID of the user who triggered the event (nullable for system events).
        scan_id: ID of the related scan (nullable).
        model_version: Version string of the model used (nullable).
        details: Human-readable description of the event. Must NOT contain
                 passwords, keys, secrets, or full medical image data.
        ip_address: Client IP address (nullable).
        success: Whether the event represents a successful action.

    Returns:
        The created AuditLog instance.
    """
    try:
        audit_entry = AuditLog(
            event_type=event_type,
            user_id=user_id,
            scan_id=scan_id,
            model_version=model_version,
            details=details,
            ip_address=ip_address,
            success=success,
        )
        db.session.add(audit_entry)
        db.session.commit()

        logger.info(
            'Audit: %s | user=%s | scan=%s | success=%s',
            event_type, user_id, scan_id, success
        )
        return audit_entry

    except Exception as e:
        logger.error('Failed to write audit log: %s', e)
        db.session.rollback()
        # Audit failures should not crash the application,
        # but they must be logged
        return None


def get_audit_logs(
    user_id=None,
    event_type=None,
    scan_id=None,
    limit=100,
):
    """
    Retrieve audit log entries with optional filtering.

    Args:
        user_id: Filter by user ID.
        event_type: Filter by event type string.
        scan_id: Filter by scan ID.
        limit: Maximum number of entries to return.

    Returns:
        List of AuditLog instances, newest first.
    """
    query = AuditLog.query

    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if event_type is not None:
        query = query.filter_by(event_type=event_type)
    if scan_id is not None:
        query = query.filter_by(scan_id=scan_id)

    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
