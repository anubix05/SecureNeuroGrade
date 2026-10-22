"""
SecureNeuroGrade — Flask Application Factory
=============================================
Central entry point for the Flask application. Initializes all
extensions, registers blueprints, and configures error handlers.

Usage:
    from app import create_app
    app = create_app()
"""

import os
import logging

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# ---------------------------------------------------------------------------
# Extension instances (initialized without app, bound in create_app)
# ---------------------------------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app(config_name=None):
    """
    Application factory.

    Args:
        config_name: One of 'development', 'production', 'testing'.
                     Defaults to FLASK_ENV or 'development'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # --- Load Configuration ------------------------------------------------
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    from app.config import config_by_name
    app.config.from_object(config_by_name[config_name])

    # --- Logging -----------------------------------------------------------
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL'], logging.INFO),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
    app.logger.info(
        'SecureNeuroGrade starting in %s mode', config_name
    )

    # --- Initialize Extensions ---------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # --- Ensure Upload Directory -------------------------------------------
    upload_path = os.path.join(app.instance_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)
    app.config['UPLOAD_FOLDER_PATH'] = upload_path

    # --- Register Blueprints -----------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.technician import technician_bp
    from app.routes.doctor import doctor_bp
    from app.routes.scans import scans_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(technician_bp, url_prefix='/technician')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(scans_bp, url_prefix='/scans')

    # --- Root & Easter Egg Routes ------------------------------------------
    from flask import redirect, url_for
    from flask_login import current_user

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_doctor:
                return redirect(url_for('doctor.dashboard'))
            elif current_user.is_technician:
                return redirect(url_for('technician.dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/easter-egg')
    def easter_egg():
        return render_template('easter_egg.html')

    # --- User Loader -------------------------------------------------------
    from app.models.database_models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Create Database Tables --------------------------------------------
    with app.app_context():
        from app.models import database_models  # noqa: F401 — ensure models are imported
        db.create_all()

    # --- Error Handlers (safe messages, no stack traces) --------------------
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('Internal server error: %s', error)
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
