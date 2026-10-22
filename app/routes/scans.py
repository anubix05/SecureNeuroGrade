"""
SecureNeuroGrade — Scan Routes
==============================
Shared scan and patient endpoints accessible by authorized users.

Endpoints:
    GET /scans/<id>              — Scan detail (role-aware view)
    GET /scans/patient/<id>      — Patient scan history
"""

import logging

from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required

from app.models.database_models import Patient, Scan

logger = logging.getLogger(__name__)

scans_bp = Blueprint('scans', __name__)


@scans_bp.route('/<int:scan_id>')
@login_required
def scan_detail(scan_id):
    """
    View scan details.

    Access rules:
        - Technicians can only view scans they uploaded.
        - Doctors can view all scans.
    """
    scan = Scan.query.get_or_404(scan_id)

    # Authorization: technicians see only their own uploads
    if current_user.is_technician and scan.uploaded_by != current_user.id:
        abort(403)

    patient = Patient.query.get_or_404(scan.patient_id)
    results = scan.results.all()

    return render_template(
        'scans/detail.html',
        scan=scan,
        patient=patient,
        results=results,
    )


@scans_bp.route('/patient/<int:patient_id>')
@login_required
def patient_scans(patient_id):
    """
    View all scans for a patient.

    Access rules:
        - Doctors can view all patient scans.
        - Technicians can only see scans they uploaded for this patient.
    """
    patient = Patient.query.get_or_404(patient_id)

    if current_user.is_doctor:
        scans = (
            Scan.query
            .filter_by(patient_id=patient_id)
            .order_by(Scan.uploaded_at.desc())
            .all()
        )
    elif current_user.is_technician:
        scans = (
            Scan.query
            .filter_by(patient_id=patient_id, uploaded_by=current_user.id)
            .order_by(Scan.uploaded_at.desc())
            .all()
        )
    else:
        abort(403)

    return render_template(
        'scans/patient_history.html',
        patient=patient,
        scans=scans,
    )
