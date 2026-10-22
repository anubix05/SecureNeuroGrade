"""
SecureNeuroGrade — Image Service
================================
Safe file handling for medical image uploads.

Security measures (per AGENTS.md §9.2):
    - Validate uploaded file types
    - Restrict upload size
    - Prevent path traversal vulnerabilities
    - Generate safe server-side filenames
    - Store uploads outside public/static directories
    - Never expose raw storage paths to clients
"""

import hashlib
import logging
import os
import uuid

from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Allowed MRI image extensions
ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'tif', 'tiff',
    'dcm',       # DICOM format
    'nii',       # NIfTI format
}


def allowed_file(filename):
    """
    Check if a filename has an allowed extension.

    Args:
        filename: The original filename from the upload.

    Returns:
        True if the extension is allowed, False otherwise.
    """
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def generate_safe_filename(original_filename):
    """
    Generate a safe, unique server-side filename.

    The original filename is sanitized and a UUID is prepended to
    prevent collisions and path traversal.

    Args:
        original_filename: The user's original filename.

    Returns:
        A safe filename string (e.g., 'a1b2c3d4_scan.jpg').
    """
    # Sanitize the original filename
    safe_name = secure_filename(original_filename)

    if not safe_name:
        safe_name = 'upload'

    # Extract extension
    if '.' in safe_name:
        name, ext = safe_name.rsplit('.', 1)
    else:
        name = safe_name
        ext = ''

    # Prepend UUID for uniqueness
    unique_id = uuid.uuid4().hex[:12]
    if ext:
        return f'{unique_id}_{name}.{ext}'
    return f'{unique_id}_{name}'


def compute_file_hash(file_path):
    """
    Compute SHA-256 hash of a file for integrity verification.

    Args:
        file_path: Path to the file.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def save_upload(file_storage, upload_folder):
    """
    Safely save an uploaded file.

    Args:
        file_storage: The werkzeug FileStorage object from the request.
        upload_folder: The directory to save the file in.

    Returns:
        dict with keys:
            - 'filename': The safe server-side filename.
            - 'original_filename': The user's original filename.
            - 'file_path': Full path to the saved file.
            - 'file_hash': SHA-256 hash of the saved file.
            - 'file_size': Size in bytes.

    Raises:
        ValueError: If the file type is not allowed or the file is empty.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError('No file provided.')

    original_filename = file_storage.filename

    if not allowed_file(original_filename):
        raise ValueError(
            f'File type not allowed. Supported formats: '
            f'{", ".join(sorted(ALLOWED_EXTENSIONS))}'
        )

    safe_name = generate_safe_filename(original_filename)
    file_path = os.path.join(upload_folder, safe_name)

    # Prevent path traversal — ensure the resolved path is within upload_folder
    real_upload_folder = os.path.realpath(upload_folder)
    real_file_path = os.path.realpath(file_path)
    if not real_file_path.startswith(real_upload_folder):
        raise ValueError('Invalid file path detected.')

    # Save the file
    file_storage.save(file_path)

    # Compute integrity hash and file size
    file_hash = compute_file_hash(file_path)
    file_size = os.path.getsize(file_path)

    if file_size == 0:
        os.remove(file_path)
        raise ValueError('Uploaded file is empty.')

    logger.info(
        'Saved upload: %s (%d bytes, hash=%s)',
        safe_name, file_size, file_hash[:16]
    )

    return {
        'filename': safe_name,
        'original_filename': original_filename,
        'file_path': file_path,
        'file_hash': file_hash,
        'file_size': file_size,
    }


def delete_file(file_path):
    """
    Safely delete a file from disk.

    Args:
        file_path: Path to the file to delete.

    Returns:
        True if deleted, False if the file didn't exist.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info('Deleted file: %s', file_path)
            return True
        return False
    except OSError as e:
        logger.error('Failed to delete file %s: %s', file_path, e)
        return False
