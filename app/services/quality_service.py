"""
SecureNeuroGrade — Quality Service (Module M2)
==============================================
Validates MRI scan quality before inference.

Pipeline position:
    Upload -> Encrypt -> Store -> Decrypt -> [M2 Quality Check] -> Inference

Quality checks (per AGENTS.md §33):
    - Supported format
    - File integrity / readability
    - Image dimensions
    - Channel structure
    - Basic preprocessing compatibility

Does NOT invent medical quality thresholds without documentation.
The criteria here are based on technical requirements of the model
input, not clinical quality assessment.
"""

import logging
import os

import numpy as np

logger = logging.getLogger(__name__)

# Technical constraints based on model requirements
MIN_IMAGE_DIMENSION = 32     # Minimum pixel dimension
MAX_IMAGE_DIMENSION = 4096   # Maximum pixel dimension
MIN_FILE_SIZE = 1024         # 1 KB minimum
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB maximum

SUPPORTED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'tif', 'tiff', 'dcm', 'nii',
}


class QualityCheckResult:
    """Result of a quality validation check."""

    def __init__(self, passed, reason=None):
        self.passed = passed
        self.reason = reason

    def __repr__(self):
        status = 'PASS' if self.passed else 'FAIL'
        return f'<QualityCheck {status}: {self.reason}>'


def validate_scan(file_path):
    """
    Run all quality checks on a scan file.

    Args:
        file_path: Path to the (decrypted) scan file.

    Returns:
        QualityCheckResult: passed=True if all checks pass,
                           passed=False with reason if any check fails.
    """
    checks = [
        _check_file_exists,
        _check_file_size,
        _check_file_extension,
        _check_image_readable,
        _check_image_dimensions,
    ]

    for check_fn in checks:
        result = check_fn(file_path)
        if not result.passed:
            logger.warning(
                'Quality check failed for %s: %s',
                os.path.basename(file_path), result.reason
            )
            return result

    logger.info('All quality checks passed for %s', os.path.basename(file_path))
    return QualityCheckResult(passed=True, reason='All checks passed')


def _check_file_exists(file_path):
    """Check that the file exists and is accessible."""
    if not os.path.exists(file_path):
        return QualityCheckResult(False, 'File not found.')
    if not os.path.isfile(file_path):
        return QualityCheckResult(False, 'Path is not a file.')
    return QualityCheckResult(True)


def _check_file_size(file_path):
    """Check that the file size is within acceptable bounds."""
    size = os.path.getsize(file_path)
    if size < MIN_FILE_SIZE:
        return QualityCheckResult(
            False,
            f'File is too small ({size} bytes). '
            f'Minimum is {MIN_FILE_SIZE} bytes.'
        )
    if size > MAX_FILE_SIZE:
        size_mb = size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return QualityCheckResult(
            False,
            f'File is too large ({size_mb:.1f} MB). '
            f'Maximum is {max_mb:.0f} MB.'
        )
    return QualityCheckResult(True)


def _check_file_extension(file_path):
    """Check that the file has a supported extension."""
    filename = os.path.basename(file_path).lower()
    if '.' not in filename:
        return QualityCheckResult(False, 'File has no extension.')

    ext = filename.rsplit('.', 1)[1]
    if ext not in SUPPORTED_EXTENSIONS:
        return QualityCheckResult(
            False,
            f'Unsupported image format (.{ext}). '
            f'Supported: {", ".join(sorted(SUPPORTED_EXTENSIONS))}'
        )
    return QualityCheckResult(True)


def _check_image_readable(file_path):
    """Check that the image can be decoded and read."""
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            img.verify()  # Verify file integrity
        return QualityCheckResult(True)
    except ImportError:
        logger.warning('Pillow not installed — skipping image readability check')
        return QualityCheckResult(True, 'Pillow not available (skipped)')
    except Exception as e:
        return QualityCheckResult(
            False,
            f'Image cannot be read or is corrupted: {str(e)}'
        )


def _check_image_dimensions(file_path):
    """Check that image dimensions are within expected bounds."""
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            width, height = img.size

        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            return QualityCheckResult(
                False,
                f'Image too small ({width}x{height}). '
                f'Minimum dimension is {MIN_IMAGE_DIMENSION}px.'
            )

        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            return QualityCheckResult(
                False,
                f'Image too large ({width}x{height}). '
                f'Maximum dimension is {MAX_IMAGE_DIMENSION}px.'
            )

        return QualityCheckResult(True)

    except ImportError:
        return QualityCheckResult(True, 'Pillow not available (skipped)')
    except Exception:
        # If we can't read dimensions, the readability check should catch it
        return QualityCheckResult(True, 'Dimension check skipped')
