"""
Unit tests for SecureNeuroGrade Quality Service (Module M2).
"""

import os
import tempfile
import unittest
from PIL import Image

from app.services.quality_service import validate_scan, QualityCheckResult


class TestQualityService(unittest.TestCase):
    """Tests for scan quality validation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for fname in os.listdir(self.temp_dir):
            try:
                os.remove(os.path.join(self.temp_dir, fname))
            except OSError:
                pass
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    def test_nonexistent_file_fails(self):
        """Test that validating a non-existent file returns a failed QualityCheckResult."""
        nonexistent = os.path.join(self.temp_dir, "does_not_exist.png")
        result = validate_scan(nonexistent)
        self.assertFalse(result.passed)
        self.assertIn("not found", result.reason.lower())

    def test_unsupported_extension_fails(self):
        """Test that unsupported extensions (e.g., .txt, .exe) fail validation."""
        bad_file = os.path.join(self.temp_dir, "scan.txt")
        with open(bad_file, "wb") as f:
            f.write(b"dummy data" * 200)
        result = validate_scan(bad_file)
        self.assertFalse(result.passed)
        self.assertIn("unsupported", result.reason.lower())

    def test_undersized_file_fails(self):
        """Test that files below the minimum size (1 KB) fail validation."""
        small_file = os.path.join(self.temp_dir, "small.png")
        with open(small_file, "wb") as f:
            f.write(b"too small")
        result = validate_scan(small_file)
        self.assertFalse(result.passed)
        self.assertIn("too small", result.reason.lower())

    def test_valid_image_passes(self):
        """Test that a standard valid image passes all quality checks."""
        img_path = os.path.join(self.temp_dir, "valid_scan.png")
        # Create a valid 512x512 RGB image with noise to exceed 1024 bytes minimum
        import numpy as np
        arr = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        img = Image.fromarray(arr)
        img.save(img_path, format="PNG")
        
        result = validate_scan(img_path)
        self.assertTrue(result.passed)
        self.assertIn("passed", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
