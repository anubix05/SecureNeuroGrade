"""
SecureNeuroGrade — Authentication Routes
========================================
Login and logout endpoints.

Endpoints:
    GET  /auth/login  — Render login page
    POST /auth/login  — Authenticate user
    POST /auth/logout — Destroy session
"""

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import current_user, login_required

from app.security.authentication import (
    authenticate_user, perform_login, perform_logout
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # Already logged in — redirect to appropriate dashboard
    if current_user.is_authenticated:
        return _redirect_to_dashboard(current_user)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html'), 400

        user = authenticate_user(username, password)

        if user is None:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html'), 401

        perform_login(user)
        flash(f'Welcome, {user.full_name}.', 'success')

        # Redirect to the originally requested page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return _redirect_to_dashboard(user)

    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout."""
    perform_logout(current_user)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_to_dashboard(user):
    """Redirect user to their role-appropriate dashboard."""
    if user.is_doctor:
        return redirect(url_for('doctor.dashboard'))
    elif user.is_technician:
        return redirect(url_for('technician.dashboard'))
    else:
        return redirect(url_for('auth.login'))
