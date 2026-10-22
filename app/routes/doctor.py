"""
SecureNeuroGrade — Doctor Routes
================================
Patient results dashboard and inference result viewing for doctors.

All routes are restricted to DOCTOR role (server-side enforcement).

Endpoints:
    GET /doctor/dashboard        — Doctor home (patient list, results)
    GET /doctor/results/<id>     — View detailed inference result
"""

import logging
import os

from flask import (
    Blueprint, abort, current_app, flash,
    render_template, request, send_file
)
from flask_login import current_user, login_required

from app.models.database_models import (
    AuditEventType, InferenceResult, Patient, Scan, ScanStatus
)
from app.security.authorization import role_required
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

doctor_bp = Blueprint('doctor', __name__)


@doctor_bp.route('/dashboard')
@login_required
@role_required('DOCTOR')
def dashboard():
    """
    Doctor dashboard — shows patients with completed scans and results.

    Prioritizes clinical readability per AGENTS.md §31.
    Makes clear that AI output is decision support.
    """
    # Get completed scans with results, newest first
    scans = (
        Scan.query
        .filter(Scan.status.in_([
            ScanStatus.COMPLETED,
            ScanStatus.ACCEPTED,
            ScanStatus.PROCESSING,
        ]))
        .order_by(Scan.uploaded_at.desc())
        .limit(100)
        .all()
    )

    return render_template('doctor/dashboard.html', scans=scans)


@doctor_bp.route('/patients')
@login_required
@role_required('DOCTOR')
def all_patients():
    """
    View all registered patients with search functionality.

    Restricted to DOCTOR role (server-side enforcement).
    """
    q = request.args.get('q', '').strip()
    query = Patient.query
    if q:
        query = query.filter(Patient.patient_identifier.ilike(f'%{q}%'))

    patients = query.order_by(Patient.patient_identifier).all()

    log_audit_event(
        event_type=AuditEventType.RESULT_VIEWED,
        user_id=current_user.id,
        details=f'Patient list accessed (search="{q}")' if q else 'Patient list accessed',
        ip_address=request.remote_addr,
    )

    return render_template('doctor/patients.html', patients=patients, query=q)


@doctor_bp.route('/results/<int:result_id>')
@login_required
@role_required('DOCTOR')
def result_detail(result_id):
    """
    View detailed inference result for a scan.

    Displays: prediction class, confidence, risk level, model version,
    and a clear disclaimer that this is decision support.
    """
    result = InferenceResult.query.get_or_404(result_id)
    scan = Scan.query.get_or_404(result.scan_id)
    patient = Patient.query.get_or_404(scan.patient_id)

    # Audit: doctor viewed a result
    log_audit_event(
        event_type=AuditEventType.RESULT_VIEWED,
        user_id=current_user.id,
        scan_id=scan.id,
        model_version=(
            result.model_version.version
            if result.model_version else 'unknown'
        ),
        ip_address=request.remote_addr,
    )

    return render_template(
        'doctor/result_detail.html',
        result=result,
        scan=scan,
        patient=patient,
    )


@doctor_bp.route('/scans/<int:scan_id>/view')
@login_required
@role_required('DOCTOR')
def view_scan_file(scan_id):
    """
    Serve the uploaded MRI scan file inline for a doctor to view.

    Security:
    - Restricted to DOCTOR role (server-side).
    - Resolves and validates the file path stays within the upload folder
      to prevent path traversal.
    - Never exposes the raw server storage path to the client.
    - Logs a RESULT_VIEWED audit event.
    """
    from app.models.database_models import Patient

    scan = Scan.query.get_or_404(scan_id)

    # Build and validate the file path
    upload_folder = current_app.config['UPLOAD_FOLDER_PATH']
    file_path = os.path.realpath(os.path.join(upload_folder, scan.filename))
    safe_root  = os.path.realpath(upload_folder)

    if not file_path.startswith(safe_root + os.sep):
        abort(403)

    if not os.path.isfile(file_path):
        abort(404)

    patient = Patient.query.get_or_404(scan.patient_id)

    log_audit_event(
        event_type=AuditEventType.RESULT_VIEWED,
        user_id=current_user.id,
        scan_id=scan.id,
        ip_address=request.remote_addr,
    )

    logger.info(
        'Doctor %s (id=%d) viewed scan file for scan_id=%d',
        current_user.username, current_user.id, scan_id
    )

    # Serve inline so the browser can display it (images open directly)
    return send_file(
        file_path,
        as_attachment=False,
        download_name=scan.original_filename,
    )
