"""
SecureNeuroGrade — Encryption Module
====================================
AES-256-GCM authenticated encryption for medical image protection.

Uses the pycryptodome library with authenticated encryption (GCM mode)
to provide both confidentiality and integrity.

SECURITY RULES (per AGENTS.md §9.3):
    - Encryption key is loaded from environment variable (never hardcoded)
    - Key is NEVER stored in frontend JavaScript
    - Key is NEVER exposed through API responses
    - Uses established cryptographic library (pycryptodome)
    - Uses authenticated encryption (AES-GCM)
"""

import logging
import os

from Crypto.Cipher import AES

logger = logging.getLogger(__name__)

# AES-256 requires a 32-byte key
AES_KEY_LENGTH = 32
GCM_NONCE_LENGTH = 12
GCM_TAG_LENGTH = 16


def _get_encryption_key():
    """
    Load the AES-256 encryption key from the environment.

    Returns:
        bytes: The 32-byte encryption key.

    Raises:
        ValueError: If the key is not set or has an invalid length.
    """
    key_hex = os.environ.get('ENCRYPTION_KEY')

    if not key_hex:
        raise ValueError(
            'ENCRYPTION_KEY environment variable is not set. '
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )

    try:
        key_bytes = bytes.fromhex(key_hex)
    except ValueError:
        raise ValueError(
            'ENCRYPTION_KEY must be a valid hex string. '
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )

    if len(key_bytes) != AES_KEY_LENGTH:
        raise ValueError(
            f'ENCRYPTION_KEY must be {AES_KEY_LENGTH} bytes '
            f'({AES_KEY_LENGTH * 2} hex characters). '
            f'Got {len(key_bytes)} bytes.'
        )

    return key_bytes


def encrypt_data(plaintext_bytes):
    """
    Encrypt data using AES-256-GCM.

    The output format is: nonce (12 bytes) || tag (16 bytes) || ciphertext

    Args:
        plaintext_bytes: The data to encrypt (bytes).

    Returns:
        bytes: nonce + tag + ciphertext concatenated.

    Raises:
        ValueError: If the encryption key is not configured.
    """
    key = _get_encryption_key()
    nonce = os.urandom(GCM_NONCE_LENGTH)

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext_bytes)

    # Format: nonce || tag || ciphertext
    return nonce + tag + ciphertext


def decrypt_data(encrypted_bytes):
    """
    Decrypt data encrypted with AES-256-GCM.

    Expects input format: nonce (12 bytes) || tag (16 bytes) || ciphertext

    Args:
        encrypted_bytes: The encrypted data (bytes).

    Returns:
        bytes: The decrypted plaintext data.

    Raises:
        ValueError: If the data is too short, the key is wrong,
                    or the data has been tampered with.
    """
    min_length = GCM_NONCE_LENGTH + GCM_TAG_LENGTH + 1
    if len(encrypted_bytes) < min_length:
        raise ValueError(
            f'Encrypted data is too short ({len(encrypted_bytes)} bytes). '
            f'Minimum is {min_length} bytes.'
        )

    key = _get_encryption_key()

    # Extract components
    nonce = encrypted_bytes[:GCM_NONCE_LENGTH]
    tag = encrypted_bytes[GCM_NONCE_LENGTH:GCM_NONCE_LENGTH + GCM_TAG_LENGTH]
    ciphertext = encrypted_bytes[GCM_NONCE_LENGTH + GCM_TAG_LENGTH:]

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    try:
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    except (ValueError, KeyError) as e:
        logger.error('Decryption failed — data may be corrupted or tampered with')
        raise ValueError(
            'Decryption failed. The data may be corrupted, the key may be '
            'wrong, or the data has been tampered with.'
        ) from e

    return plaintext


def encrypt_file(input_path, output_path):
    """
    Encrypt a file on disk using AES-256-GCM.

    Args:
        input_path: Path to the plaintext file.
        output_path: Path to write the encrypted file.
    """
    with open(input_path, 'rb') as f:
        plaintext = f.read()

    encrypted = encrypt_data(plaintext)

    with open(output_path, 'wb') as f:
        f.write(encrypted)

    logger.info('Encrypted file: %s -> %s', input_path, output_path)


def decrypt_file(input_path, output_path):
    """
    Decrypt an AES-256-GCM encrypted file.

    Args:
        input_path: Path to the encrypted file.
        output_path: Path to write the decrypted file.
    """
    with open(input_path, 'rb') as f:
        encrypted = f.read()

    plaintext = decrypt_data(encrypted)

    with open(output_path, 'wb') as f:
        f.write(plaintext)

    logger.info('Decrypted file: %s -> %s', input_path, output_path)
