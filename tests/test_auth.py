"""
Unit tests for SecureNeuroGrade Authentication & Authorization Models.
"""

import unittest
from app import create_app, bcrypt
from app.models.database_models import UserRole
from app.security.authentication import hash_password, verify_password


class TestAuthModule(unittest.TestCase):
    """Tests for authentication security and password handling."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test_password_hashing_and_verification(self):
        """Test bcrypt hash generation and correct verification."""
        password = "SecureDoctorPassword2026!"
        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))
        self.assertTrue(verify_password(hashed, password))
        self.assertFalse(verify_password(hashed, "WrongPassword123"))

    def test_user_roles_defined(self):
        """Ensure all required roles per AGENTS.md are defined."""
        self.assertEqual(UserRole.DOCTOR, "DOCTOR")
        self.assertEqual(UserRole.LAB_TECHNICIAN, "LAB_TECHNICIAN")


if __name__ == "__main__":
    unittest.main()
