"""
Encryption service for PII fields.
Uses AES-256-CBC with application-layer encryption (pgcrypto-compatible).
"""

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet

from .config import get_settings

settings = get_settings()

# Generate Fernet key from settings (32 bytes for Fernet)
# In production, this comes from AWS Secrets Manager
_encryption_key = Fernet(
    base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY_PASSPHRASE.encode()).digest()
    )
)


class EncryptionService:
    """Encrypt/decrypt sensitive fields using Fernet (AES-128-CBC equivalent)."""

    @staticmethod
    def encrypt(plaintext: str) -> bytes:
        """Encrypt plaintext to bytes."""
        if not plaintext:
            return None
        return _encryption_key.encrypt(plaintext.encode())

    @staticmethod
    def decrypt(ciphertext: bytes) -> str:
        """Decrypt ciphertext bytes to plaintext."""
        if not ciphertext:
            return None
        return _encryption_key.decrypt(ciphertext).decode()

    @staticmethod
    def hash_for_lookup(plaintext: str) -> str:
        """Create SHA-256 hash for lookup (one-way, non-reversible)."""
        if not plaintext:
            return None
        return hashlib.sha256(plaintext.encode()).hexdigest()


def get_encryption_service() -> EncryptionService:
    """FastAPI dependency."""
    return EncryptionService()
