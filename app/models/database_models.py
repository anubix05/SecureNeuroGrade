"""
SecureNeuroGrade — Database Models
==================================
SQLAlchemy ORM models for all core entities.

Entities:
    - User          : Doctors and lab technicians
    - Patient       : Anonymized patient records
    - Scan          : MRI scan uploads and their processing status
    - InferenceResult : AI model prediction output
    - AuditLog      : Security and workflow event log
    - ModelVersion  : ML model version registry

Relationships (per AGENTS.md §11):
    User --uploads--> Scan --belongs_to--> Patient
    Scan --produces--> InferenceResult --uses--> ModelVersion
    User/System --creates--> AuditLog
"""

from datetime import datetime, timezone

from flask_login import UserMixin

from app import db


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class UserRole:
    """User role constants."""
    LAB_TECHNICIAN = 'LAB_TECHNICIAN'
    DOCTOR = 'DOCTOR'

    ALL = [LAB_TECHNICIAN, DOCTOR]


class ScanStatus:
    """Scan processing status constants."""
    UPLOADED = 'UPLOADED'
    ENCRYPTING = 'ENCRYPTING'
    VALIDATING = 'VALIDATING'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class RiskLevel:
    """Tumor risk level constants."""
    LOW = 'LOW'
    MODERATE = 'MODERATE'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


class AuditEventType:
    """Audit log event types."""
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILURE = 'LOGIN_FAILURE'
    LOGOUT = 'LOGOUT'
    SCAN_UPLOADED = 'SCAN_UPLOADED'
    SCAN_REJECTED = 'SCAN_REJECTED'
    SCAN_ACCEPTED = 'SCAN_ACCEPTED'
    INFERENCE_STARTED = 'INFERENCE_STARTED'
    INFERENCE_COMPLETED = 'INFERENCE_COMPLETED'
    INFERENCE_FAILED = 'INFERENCE_FAILED'
    RESULT_VIEWED = 'RESULT_VIEWED'
    ACCESS_DENIED = 'ACCESS_DENIED'


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    """
    Application user — either a lab technician or a doctor.
    Passwords are never stored in plaintext (bcrypt hash).
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # LAB_TECHNICIAN or DOCTOR
    full_name = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    scans = db.relationship('Scan', backref='uploader', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    @property
    def is_doctor(self):
        return self.role == UserRole.DOCTOR

    @property
    def is_technician(self):
        return self.role == UserRole.LAB_TECHNICIAN


class Patient(db.Model):
    """
    Anonymized patient record.
    No real patient-identifying information should be stored.
    """
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_identifier = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    scans = db.relationship('Scan', backref='patient', lazy='dynamic')

    def __repr__(self):
        return f'<Patient {self.patient_identifier}>'


class Scan(db.Model):
    """
    MRI scan upload record.
    Tracks the full lifecycle: upload → encryption → validation →
    inference → result.
    """
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey('patients.id'), nullable=False
    )
    uploaded_by = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)        # Safe server-side name
    original_filename = db.Column(db.String(255), nullable=False)  # User's original name
    file_hash = db.Column(db.String(64), nullable=True)           # SHA-256 integrity hash
    file_size = db.Column(db.Integer, nullable=True)              # Bytes
    organ_type = db.Column(db.String(50), default='brain', nullable=False)
    status = db.Column(
        db.String(20), default=ScanStatus.UPLOADED, nullable=False
    )
    rejection_reason = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    processed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    results = db.relationship(
        'InferenceResult', backref='scan', lazy='dynamic'
    )

    def __repr__(self):
        return f'<Scan {self.id} [{self.status}]>'


class InferenceResult(db.Model):
    """
    AI model prediction output for a scan.

    Note: This is a model prediction, NOT a confirmed medical diagnosis.
    The confidence_score represents the model's output probability and
    should not be interpreted as clinical certainty.
    """
    __tablename__ = 'inference_results'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(
        db.Integer, db.ForeignKey('scans.id'), nullable=False
    )
    model_version_id = db.Column(
        db.Integer, db.ForeignKey('model_versions.id'), nullable=True
    )
    prediction_class = db.Column(db.String(100), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=True)
    raw_output_json = db.Column(db.Text, nullable=True)  # JSON string of full model output
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    model_version = db.relationship('ModelVersion', backref='results')

    def __repr__(self):
        return f'<InferenceResult scan={self.scan_id} class={self.prediction_class}>'


class AuditLog(db.Model):
    """
    Security and workflow audit log.
    Captures events like logins, uploads, inference runs, and access attempts.

    Never logs passwords, encryption keys, session secrets, or full
    medical images.
    """
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )
    scan_id = db.Column(
        db.Integer, db.ForeignKey('scans.id'), nullable=True
    )
    model_version = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    success = db.Column(db.Boolean, default=True, nullable=False)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True
    )

    def __repr__(self):
        return f'<AuditLog {self.event_type} at {self.timestamp}>'


class ModelVersion(db.Model):
    """
    ML model version registry.
    Tracks model metadata for reproducibility and audit trails.

    Designed for multi-organ extensibility: organ_type allows different
    models per organ (brain, lung, liver, etc.) without schema changes.
    """
    __tablename__ = 'model_versions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    organ_type = db.Column(db.String(50), default='brain', nullable=False)
    description = db.Column(db.Text, nullable=True)
    checkpoint_path = db.Column(db.String(500), nullable=True)
    dataset_version = db.Column(db.String(50), nullable=True)
    classes_json = db.Column(db.Text, nullable=True)  # JSON list of class names
    training_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f'<ModelVersion {self.name}-{self.version} ({self.organ_type})>'
