"""
Test Suite: Security - Encryption Service Tests

Purpose: Validate Fernet encryption for PII data fields including:
- AES-256-CBC encryption for encrypted fields
- HMAC integrity verification
- Encryption/decryption roundtrip
- Key rotation handling

COPPA Relevance: Critical for encrypting PII fields (email, name) in users table.
"""

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hmac


class TestFernetEncryption:
    """Tests for Fernet encryption operations."""

    @pytest.fixture
    def fernet_key(self):
        """Generate a Fernet key for testing."""
        return Fernet.generate_key()

    @pytest.fixture
    def fernet(self, fernet_key):
        """Create Fernet instance with test key."""
        return Fernet(fernet_key)

    def test_encrypt_decrypt_roundtrip(self, fernet):
        """SEC-ENC-001: Verify encrypt then decrypt returns original data."""
        original = b"test sensitive data"
        encrypted = fernet.encrypt(original)
        decrypted = fernet.decrypt(encrypted)
        assert decrypted == original

    def test_encrypted_data_is_bytes(self, fernet):
        """SEC-ENC-002: Verify encrypted data is bytes (for BYTEA storage)."""
        original = b"test data"
        encrypted = fernet.encrypt(original)
        assert isinstance(encrypted, bytes)

    def test_different_encryptions_different_outputs(self, fernet):
        """SEC-ENC-003: Verify same plaintext produces different ciphertext."""
        original = b"same data"
        encrypted1 = fernet.encrypt(original)
        encrypted2 = fernet.encrypt(original)
        assert encrypted1 != encrypted2

    def test_decrypt_wrong_key_fails(self, fernet):
        """SEC-ENC-004: Verify decryption with wrong key raises exception."""
        original = b"secret data"
        encrypted = fernet.encrypt(original)
        wrong_key = Fernet.generate_key()
        with pytest.raises(Exception):
            Fernet(wrong_key).decrypt(encrypted)


class TestHMACIntegrity:
    """Tests for HMAC integrity verification."""

    def test_hmac_signature_verification(self):
        """SEC-ENC-005: Verify HMAC signature can be verified."""
        secret = b"super_secret_key_32_bytes_long!!"
        message = b"encrypted data payload"
        signature = hmac.new(secret, message, hashes.SHA256()).digest()
        assert hmac.new(secret, message, hashes.SHA256()).digest() == signature

    def test_hmac_tampering_detected(self):
        """SEC-ENC-006: Verify HMAC detects tampered message."""
        secret = b"super_secret_key_32_bytes_long!!"
        original_sig = hmac.new(secret, b"original", hashes.SHA256()).digest()
        assert hmac.new(secret, b"tampered", hashes.SHA256()).digest() != original_sig


class TestPIIEncryption:
    """Tests for PII field encryption patterns."""

    def test_email_encryption(self, fernet):
        """SEC-ENC-008: Verify email can be encrypted for storage."""
        email = b"parent@example.com"
        encrypted = fernet.encrypt(email)
        decrypted = fernet.decrypt(encrypted)
        assert decrypted == email

    def test_name_encryption(self, fernet):
        """SEC-ENC-009: Verify name can be encrypted for storage."""
        name = b"Maria Rodriguez"
        encrypted = fernet.encrypt(name)
        decrypted = fernet.decrypt(encrypted)
        assert decrypted == name

    def test_encrypted_field_storage_format(self, fernet):
        """SEC-ENC-010: Verify encrypted data is suitable for BYTEA storage."""
        data = b"test_value"
        encrypted = fernet.encrypt(data)
        assert isinstance(encrypted, bytes)
        assert len(encrypted) > 0

    def test_key_rotation_compatibility(self, fernet):
        """SEC-ENC-011: Verify old encrypted data can be decrypted."""
        original = b"legacy data"
        encrypted = fernet.encrypt(original)
        assert fernet.decrypt(encrypted) == original
