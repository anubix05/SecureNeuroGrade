"""
Unit tests for SecureNeuroGrade Flask Application Factory & Core Endpoints.
"""

import unittest
from app import create_app, db


class TestAppFactory(unittest.TestCase):
    """Tests for application factory and baseline routing."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_page_renders(self):
        """Test that the login page loads with HTTP 200."""
        response = self.client.get("/auth/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SecureNeuroGrade", response.data)

    def test_unauthorized_dashboard_redirects_to_login(self):
        """Test that unauthenticated requests to protected dashboards redirect."""
        response = self.client.get("/doctor/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()
