"""
Unit tests for SecureNeuroGrade Encryption Module (Module M1).
"""

import os
import unittest
from app.security.encryption import encrypt_data, decrypt_data, AES_KEY_LENGTH


class TestEncryptionModule(unittest.TestCase):
    """Tests for AES-256-GCM encryption and decryption."""

    def setUp(self):
        # 32-byte test hex key
        self.test_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        os.environ["ENCRYPTION_KEY"] = self.test_key

    def test_encrypt_decrypt_roundtrip(self):
        """Test that data can be encrypted and successfully decrypted back to plaintext."""
        original_data = b"Patient MRI Scan Data - Strictly Confidential"
        ciphertext = encrypt_data(original_data)
        
        self.assertNotEqual(original_data, ciphertext)
        self.assertGreater(len(ciphertext), len(original_data))

        decrypted = decrypt_data(ciphertext)
        self.assertEqual(original_data, decrypted)

    def test_tampered_ciphertext_fails(self):
        """Test that tampering with ciphertext triggers an authentication failure."""
        original_data = b"Confidential Medical Scan Content"
        ciphertext = bytearray(encrypt_data(original_data))
        
        # Tamper with the last byte
        ciphertext[-1] ^= 0xFF

        with self.assertRaises(ValueError):
            decrypt_data(bytes(ciphertext))

    def test_short_data_rejected(self):
        """Test that ciphertext shorter than nonce + tag length is rejected."""
        short_data = b"short"
        with self.assertRaises(ValueError):
            decrypt_data(short_data)


if __name__ == "__main__":
    unittest.main()
