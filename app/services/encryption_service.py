"""
SecureNeuroGrade — Encryption Service (Module M1)
=================================================
Orchestrates encryption and decryption of medical images during
the upload and inference pipeline.

Pipeline position:
    Upload -> [M1 Encrypt] -> Store -> [M1 Decrypt] -> Quality Check -> Inference

Uses AES-256-GCM from app.security.encryption.
"""

import logging
import os

from app.security.encryption import encrypt_file, decrypt_file

logger = logging.getLogger(__name__)


def encrypt_scan(plaintext_path, encrypted_dir):
    """
    Encrypt an uploaded MRI scan for secure storage.

    Args:
        plaintext_path: Path to the original (plaintext) scan file.
        encrypted_dir: Directory to store the encrypted file.

    Returns:
        str: Path to the encrypted file.

    Raises:
        FileNotFoundError: If the plaintext file doesn't exist.
        ValueError: If the encryption key is not configured.
    """
    if not os.path.exists(plaintext_path):
        raise FileNotFoundError(f'Scan file not found: {plaintext_path}')

    os.makedirs(encrypted_dir, exist_ok=True)

    basename = os.path.basename(plaintext_path)
    encrypted_path = os.path.join(encrypted_dir, f'{basename}.enc')

    encrypt_file(plaintext_path, encrypted_path)
    logger.info('Scan encrypted: %s', basename)

    return encrypted_path


def decrypt_scan(encrypted_path, decrypted_dir):
    """
    Decrypt a stored MRI scan for inference processing.

    Args:
        encrypted_path: Path to the encrypted scan file.
        decrypted_dir: Directory to store the decrypted file.

    Returns:
        str: Path to the decrypted file.

    Raises:
        FileNotFoundError: If the encrypted file doesn't exist.
        ValueError: If decryption fails (wrong key or tampered data).
    """
    if not os.path.exists(encrypted_path):
        raise FileNotFoundError(f'Encrypted file not found: {encrypted_path}')

    os.makedirs(decrypted_dir, exist_ok=True)

    # Remove .enc extension for the decrypted filename
    basename = os.path.basename(encrypted_path)
    if basename.endswith('.enc'):
        basename = basename[:-4]

    decrypted_path = os.path.join(decrypted_dir, basename)

    decrypt_file(encrypted_path, decrypted_path)
    logger.info('Scan decrypted for processing: %s', basename)

    return decrypted_path
