# Encryption Design

## Overview

SecureNeuroGrade uses **AES-256-GCM** (Galois/Counter Mode) for medical image encryption. This provides both **confidentiality** (data secrecy) and **integrity** (tamper detection).

## Why AES-256-GCM?

- **AES-256**: Industry-standard symmetric encryption with 256-bit key strength
- **GCM mode**: Authenticated encryption — detects if encrypted data has been modified
- **Established library**: Uses `pycryptodome`, a widely-used and maintained Python cryptographic library
- **No custom crypto**: We do not invent custom cryptographic algorithms (per AGENTS.md §9.3)

## Key Management

### Rules
- Encryption key is **never hardcoded** in source code
- Key is loaded from `ENCRYPTION_KEY` environment variable
- Key is **never stored** in frontend JavaScript
- Key is **never exposed** through API responses
- Key is **never committed** to version control

### Key Format
- 32 bytes (256 bits), hex-encoded (64 hex characters)
- Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

## Encrypted Data Format

```
┌──────────┬──────────┬───────────────────┐
│  Nonce   │   Tag    │    Ciphertext     │
│ 12 bytes │ 16 bytes │   variable len    │
└──────────┴──────────┴───────────────────┘
```

- **Nonce** (12 bytes): Random value, unique per encryption operation
- **Tag** (16 bytes): Authentication tag for integrity verification
- **Ciphertext**: The encrypted data

## Implementation

| Component | File |
|-----------|------|
| Core encryption/decryption | `app/security/encryption.py` |
| Service layer (scan encrypt/decrypt) | `app/services/encryption_service.py` |

## Security Considerations

1. Each encryption operation uses a fresh random nonce
2. Decryption verifies the authentication tag before returning data
3. If data has been tampered with, decryption raises a `ValueError`
4. The encryption key must be kept secret and rotated periodically
5. Encrypted files use the `.enc` extension
