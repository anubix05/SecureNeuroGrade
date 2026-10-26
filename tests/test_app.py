"""
Unit tests for SecureNeuroGrade Flask Application Factory & Core Endpoints.
"""

import unittest
from app import create_app, db
from app.models.database_models import User, UserRole


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

    def _login_as_technician(self):
        with self.app.app_context():
            user = User(
                username="test-technician",
                email="technician@example.test",
                password_hash="not-used-by-test-client",
                role=UserRole.LAB_TECHNICIAN,
                full_name="Test Technician",
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True

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

    def test_upload_page_lists_registered_scan_types(self):
        self._login_as_technician()
        response = self.client.get("/technician/upload-scan")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<option value="brain">Brain tumor</option>', response.data)
        self.assertIn(b'<option value="liver">Liver tumor</option>', response.data)

    def test_upload_rejects_unregistered_organ_type(self):
        self._login_as_technician()
        response = self.client.post(
            "/technician/upload",
            data={"patient_identifier": "PT-TEST-001", "organ_type": "kidney"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Select a supported scan type.", response.data)


if __name__ == "__main__":
    unittest.main()
