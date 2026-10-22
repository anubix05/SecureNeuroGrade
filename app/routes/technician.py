"""
SecureNeuroGrade — Lab Technician Routes
========================================
MRI scan upload and status monitoring for lab technicians.

All routes are restricted to LAB_TECHNICIAN role (server-side enforcement).

Endpoints:
    GET  /technician/dashboard — Technician home (upload form, scan list)
    POST /technician/upload    — Upload an MRI scan
    GET  /technician/status/<id> — View scan processing status
"""

import json
import logging
import os
from datetime import datetime, timezone

from flask import (
    Blueprint, current_app, flash, redirect,
    render_template, request, url_for
)
from flask_login import current_user, login_required

from app import db
from app.models.database_models import (
    AuditEventType, InferenceResult, ModelVersion, Patient, Scan, ScanStatus
)
from app.security.authorization import role_required
from app.services.audit_service import log_audit_event
from app.services.classification_service import classify_result
from app.services.image_service import save_upload
from app.services.inference_service import run_inference
from app.services.quality_service import validate_scan

logger = logging.getLogger(__name__)

technician_bp = Blueprint('technician', __name__)


@technician_bp.route('/dashboard')
@login_required
@role_required('LAB_TECHNICIAN')
def dashboard():
    """Technician dashboard — recent scan uploads (upload form is on a separate page)."""
    scans = (
        Scan.query
        .filter_by(uploaded_by=current_user.id)
        .order_by(Scan.uploaded_at.desc())
        .limit(50)
        .all()
    )
    return render_template('technician/dashboard.html', scans=scans)


@technician_bp.route('/upload-scan')
@login_required
@role_required('LAB_TECHNICIAN')
def upload_scan_page():
    """Standalone MRI scan upload page."""
    return render_template('technician/upload_scan_page.html')


@technician_bp.route('/upload', methods=['POST'])
@login_required
@role_required('LAB_TECHNICIAN')
def upload_scan():
    """
    Handle MRI scan upload.

    Validates the file, saves it securely, creates database records,
    and runs quality checks.
    """
    # --- Validate patient identifier ---
    patient_identifier = request.form.get('patient_identifier', '').strip()
    if not patient_identifier:
        flash('Patient identifier is required.', 'danger')
        return redirect(url_for('technician.upload_scan_page'))

    # --- Validate file upload ---
    if 'scan_file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('technician.upload_scan_page'))

    file = request.files['scan_file']
    if not file or not file.filename:
        flash('No file selected.', 'danger')
        return redirect(url_for('technician.upload_scan_page'))

    # --- Save the file securely ---
    upload_folder = current_app.config['UPLOAD_FOLDER_PATH']
    try:
        file_info = save_upload(file, upload_folder)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('technician.upload_scan_page'))

    # --- Find or create patient record ---
    patient = Patient.query.filter_by(
        patient_identifier=patient_identifier
    ).first()

    if patient is None:
        patient = Patient(
            patient_identifier=patient_identifier,
            age=request.form.get('patient_age', type=int),
            gender=request.form.get('patient_gender', '').strip() or None,
        )
        db.session.add(patient)
        db.session.flush()  # Get patient.id before creating scan

    # --- Create scan record ---
    scan = Scan(
        patient_id=patient.id,
        uploaded_by=current_user.id,
        filename=file_info['filename'],
        original_filename=file_info['original_filename'],
        file_hash=file_info['file_hash'],
        file_size=file_info['file_size'],
        organ_type='brain',
        status=ScanStatus.UPLOADED,
    )
    db.session.add(scan)
    db.session.commit()

    # --- Audit log ---
    log_audit_event(
        event_type=AuditEventType.SCAN_UPLOADED,
        user_id=current_user.id,
        scan_id=scan.id,
        details=f'File: {file_info["original_filename"]}, '
                f'Size: {file_info["file_size"]} bytes',
        ip_address=request.remote_addr,
    )

    # --- Run quality validation ---
    file_path = os.path.join(upload_folder, file_info['filename'])
    scan.status = ScanStatus.VALIDATING
    db.session.commit()

    quality_result = validate_scan(file_path)

    if quality_result.passed:
        scan.status = ScanStatus.ACCEPTED
        db.session.commit()

        log_audit_event(
            event_type=AuditEventType.SCAN_ACCEPTED,
            user_id=current_user.id,
            scan_id=scan.id,
        )

        # --- Run AI Inference & Result Classification ---
        try:
            scan.status = ScanStatus.PROCESSING
            db.session.commit()

            log_audit_event(
                event_type=AuditEventType.INFERENCE_STARTED,
                user_id=current_user.id,
                scan_id=scan.id,
            )

            raw_inference = run_inference(file_path, organ_type=scan.organ_type)
            classified = classify_result(raw_inference)

            # Retrieve active model version metadata
            model_ver = ModelVersion.query.filter_by(
                organ_type=scan.organ_type, is_active=True
            ).first()

            result_record = InferenceResult(
                scan_id=scan.id,
                model_version_id=model_ver.id if model_ver else None,
                prediction_class=classified['prediction_class'],
                confidence_score=classified['confidence_score'],
                risk_level=classified['risk_level'],
                raw_output_json=json.dumps(classified['all_predictions']),
            )
            db.session.add(result_record)

            scan.status = ScanStatus.COMPLETED
            db.session.commit()

            log_audit_event(
                event_type=AuditEventType.INFERENCE_COMPLETED,
                user_id=current_user.id,
                scan_id=scan.id,
                model_version=model_ver.version if model_ver else 'placeholder',
            )
            flash('Scan uploaded, validated, and analyzed by AI pipeline.', 'success')

        except Exception as e:
            logger.error('Inference pipeline failed for scan %s: %s', scan.id, e)
            scan.status = ScanStatus.FAILED
            scan.rejection_reason = f"[Stage: AI Model Inference & Classification (Module M3)] {str(e)}"
            db.session.commit()

            log_audit_event(
                event_type=AuditEventType.INFERENCE_FAILED,
                user_id=current_user.id,
                scan_id=scan.id,
                details=scan.rejection_reason,
                success=False,
            )
            flash('Scan uploaded and accepted, but AI analysis failed.', 'warning')
    else:
        scan.status = ScanStatus.REJECTED
        scan.rejection_reason = f"[Stage: Scan Quality Checker (Module M2)] {quality_result.reason}"
        log_audit_event(
            event_type=AuditEventType.SCAN_REJECTED,
            user_id=current_user.id,
            scan_id=scan.id,
            details=scan.rejection_reason,
            success=False,
        )
        flash(
            f'Scan rejected: {quality_result.reason}. Please re-upload.',
            'warning'
        )

    db.session.commit()

    return redirect(url_for('technician.upload_status', scan_id=scan.id))


@technician_bp.route('/status/<int:scan_id>')
@login_required
@role_required('LAB_TECHNICIAN')
def upload_status(scan_id):
    """View the processing status of a specific scan."""
    scan = Scan.query.get_or_404(scan_id)

    # Technicians can only view their own uploads
    if scan.uploaded_by != current_user.id:
        flash('You do not have access to this scan.', 'danger')
        return redirect(url_for('technician.dashboard')), 403

    return render_template('technician/upload_status.html', scan=scan)


@technician_bp.route('/retry/<int:scan_id>', methods=['GET', 'POST'])
@login_required
@role_required('LAB_TECHNICIAN')
def retry_scan(scan_id):
    """
    Retry/re-upload a corrected file for a REJECTED or FAILED scan.
    """
    scan = Scan.query.get_or_404(scan_id)

    # Authorization: technicians can only retry their own uploads
    if scan.uploaded_by != current_user.id:
        flash('You do not have access to this scan.', 'danger')
        return redirect(url_for('technician.dashboard')), 403

    # Only scans in REJECTED or FAILED status can be retried
    if scan.status not in [ScanStatus.REJECTED, ScanStatus.FAILED]:
        flash('Only rejected or failed scans can be retried.', 'info')
        return redirect(url_for('technician.upload_status', scan_id=scan.id))

    patient = Patient.query.get_or_404(scan.patient_id)

    if request.method == 'GET':
        return render_template('technician/retry_upload.html', scan=scan, patient=patient)

    # POST: Process new corrected file
    if 'scan_file' not in request.files:
        flash('No file selected for re-upload.', 'danger')
        return redirect(url_for('technician.retry_scan', scan_id=scan.id))

    file = request.files['scan_file']
    if not file or not file.filename:
        flash('No file selected for re-upload.', 'danger')
        return redirect(url_for('technician.retry_scan', scan_id=scan.id))

    upload_folder = current_app.config['UPLOAD_FOLDER_PATH']
    try:
        file_info = save_upload(file, upload_folder)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('technician.retry_scan', scan_id=scan.id))

    # Update patient optional demographic info if modified
    patient.age = request.form.get('patient_age', type=int) or patient.age
    patient.gender = request.form.get('patient_gender', '').strip() or patient.gender

    # Reset scan record with new file details
    scan.filename = file_info['filename']
    scan.original_filename = file_info['original_filename']
    scan.file_hash = file_info['file_hash']
    scan.file_size = file_info['file_size']
    scan.rejection_reason = None
    scan.status = ScanStatus.UPLOADED
    db.session.commit()

    log_audit_event(
        event_type=AuditEventType.SCAN_UPLOADED,
        user_id=current_user.id,
        scan_id=scan.id,
        details=f'RETRY upload for Scan #{scan.id}. New file: {file_info["original_filename"]}',
        ip_address=request.remote_addr,
    )

    # Run quality validation
    file_path = os.path.join(upload_folder, file_info['filename'])
    scan.status = ScanStatus.VALIDATING
    db.session.commit()

    quality_result = validate_scan(file_path)

    if quality_result.passed:
        scan.status = ScanStatus.ACCEPTED
        db.session.commit()

        log_audit_event(
            event_type=AuditEventType.SCAN_ACCEPTED,
            user_id=current_user.id,
            scan_id=scan.id,
        )

        # Trigger AI inference pipeline
        try:
            scan.status = ScanStatus.PROCESSING
            db.session.commit()

            log_audit_event(
                event_type=AuditEventType.INFERENCE_STARTED,
                user_id=current_user.id,
                scan_id=scan.id,
            )

            raw_inference = run_inference(file_path, organ_type=scan.organ_type)
            classified = classify_result(raw_inference)

            model_ver = ModelVersion.query.filter_by(
                organ_type=scan.organ_type, is_active=True
            ).first()

            result_record = InferenceResult(
                scan_id=scan.id,
                model_version_id=model_ver.id if model_ver else None,
                prediction_class=classified['prediction_class'],
                confidence_score=classified['confidence_score'],
                risk_level=classified['risk_level'],
                raw_output_json=json.dumps(classified['all_predictions']),
            )
            db.session.add(result_record)

            scan.status = ScanStatus.COMPLETED
            db.session.commit()

            log_audit_event(
                event_type=AuditEventType.INFERENCE_COMPLETED,
                user_id=current_user.id,
                scan_id=scan.id,
                model_version=model_ver.version if model_ver else 'placeholder',
            )
            flash('Scan re-uploaded, validated, and analyzed by AI pipeline.', 'success')

        except Exception as e:
            logger.error('Inference pipeline failed for retry scan %s: %s', scan.id, e)
            scan.status = ScanStatus.FAILED
            scan.rejection_reason = f"[Stage: AI Model Inference & Classification (Module M3)] {str(e)}"
            db.session.commit()

            log_audit_event(
                event_type=AuditEventType.INFERENCE_FAILED,
                user_id=current_user.id,
                scan_id=scan.id,
                details=scan.rejection_reason,
                success=False,
            )
            flash('Scan re-uploaded and accepted, but AI analysis failed.', 'warning')
    else:
        scan.status = ScanStatus.REJECTED
        scan.rejection_reason = f"[Stage: Scan Quality Checker (Module M2)] {quality_result.reason}"
        log_audit_event(
            event_type=AuditEventType.SCAN_REJECTED,
            user_id=current_user.id,
            scan_id=scan.id,
            details=scan.rejection_reason,
            success=False,
        )
        flash(f'Retry scan rejected: {quality_result.reason}. Please select a valid scan.', 'warning')

    db.session.commit()
    return redirect(url_for('technician.upload_status', scan_id=scan.id))
