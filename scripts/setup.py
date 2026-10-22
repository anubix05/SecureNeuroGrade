"""
SecureNeuroGrade — Database Setup Script
========================================
Initializes the database and optionally seeds development data.

Usage:
    python scripts/setup.py          # Create tables only
    python scripts/setup.py --seed   # Create tables + seed dev data

The seeded accounts are for DEVELOPMENT ONLY:
    - doctor / doctor123     (DOCTOR role)
    - technician / tech123   (LAB_TECHNICIAN role)

NEVER use these credentials in production.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.database_models import User, UserRole, ModelVersion
from app.security.authentication import hash_password


def init_database(app):
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        print('[OK] Database tables created successfully.')


def seed_dev_data(app):
    """
    Seed development data.

    Creates test accounts and a placeholder model version.
    These are for DEVELOPMENT ONLY — never use in production.
    """
    with app.app_context():
        # Check if data already exists
        if User.query.first() is not None:
            print('[INFO] Database already contains data. Skipping seed.')
            return

        # Create test doctor account
        doctor = User(
            username='doctor',
            email='doctor@example.com',
            password_hash=hash_password('doctor123'),
            role=UserRole.DOCTOR,
            full_name='Dr. Test Doctor',
            is_active=True,
        )

        # Create test technician account
        technician = User(
            username='technician',
            email='technician@example.com',
            password_hash=hash_password('tech123'),
            role=UserRole.LAB_TECHNICIAN,
            full_name='Test Technician',
            is_active=True,
        )

        # Create placeholder model version
        model_version = ModelVersion(
            name='brain-tumor-cnn',
            version='v0.1-placeholder',
            organ_type='brain',
            description=(
                'Placeholder model version for development. '
                'No trained checkpoint — inference returns mock results.'
            ),
            is_active=True,
        )

        db.session.add_all([doctor, technician, model_version])
        db.session.commit()

        print('[OK] Development seed data created:')
        print('   Doctor:     doctor / doctor123')
        print('   Technician: technician / tech123')
        print('   Model:      brain-tumor-cnn v0.1-placeholder')
        print()
        print('[WARNING] These credentials are for DEVELOPMENT ONLY.')


if __name__ == '__main__':
    if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    app = create_app('development')

    init_database(app)

    if '--seed' in sys.argv:
        seed_dev_data(app)
    else:
        print('[INFO] Run with --seed to create test accounts.')
