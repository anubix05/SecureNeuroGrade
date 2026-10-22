"""
SecureNeuroGrade — Application Configuration
=============================================
Environment-driven configuration. All secrets are loaded from
environment variables (never hardcoded).

Usage:
    from app.config import config_by_name
    app.config.from_object(config_by_name['development'])
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration with shared defaults."""

    # --- Flask Core ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-insecure-default')
    
    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///secureneurograde.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Security / Encryption ---
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

    # --- Upload Configuration ---
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 50)) * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'tif', 'tiff',
        'dcm',   # DICOM
        'nii',   # NIfTI
        'nii.gz',
    }

    # --- Logging ---
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # --- Session ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in local dev


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
