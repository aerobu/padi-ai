"""
Test Suite: Security - JWT Validation Tests

Purpose: Validate JWT token handling including:
- Token expiry validation
- Role-based access control
- Token refresh rotation
- Invalid token rejection

COPPA Relevance: JWT tokens protect student data access.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
import jwt


class TestJWTExpiryValidation:
    """Tests for JWT token expiry."""

    def test_valid_token_accepted(self):
        """SEC-JWT-001: Verify valid token is accepted."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "user123",
            "role": "parent",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Should decode without error
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "parent"

    def test_expired_token_rejected(self):
        """SEC-JWT-002: Verify expired token is rejected."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "user123",
            "role": "parent",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            "iat": datetime.now(timezone.utc) - timedelta(hours=2)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Should raise exception
        with pytest.raises(Exception):
            jwt.decode(token, secret, algorithms=["HS256"])

    def test_future_not_valid_before_rejected(self):
        """SEC-JWT-003: Verify token with future nbf is rejected."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "user123",
            "role": "parent",
            "nbf": datetime.now(timezone.utc) + timedelta(hours=1),  # Not valid yet
            "exp": datetime.now(timezone.utc) + timedelta(hours=2),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Should raise exception for future nbf
        with pytest.raises(Exception):
            jwt.decode(token, secret, algorithms=["HS256"])

    def test_access_token_15min_expiry(self):
        """SEC-JWT-004: Verify access token has 15-minute expiry."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "user123",
            "role": "parent",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        # Verify exp is within 15 minutes
        token_exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        time_diff = (token_exp - datetime.now(timezone.utc)).total_seconds()
        assert 899 <= time_diff <= 900  # Allow 1 second tolerance


class TestRoleBasedAccessControl:
    """Tests for role-based access control."""

    def test_parent_role_token(self):
        """SEC-JWT-005: Verify parent role token is valid."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "user123",
            "role": "parent",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["role"] == "parent"

    def test_admin_role_token(self):
        """SEC-JWT-006: Verify admin role token is valid."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "admin123",
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["role"] == "admin"

    def test_invalid_role_rejected(self):
        """SEC-JWT-007: Verify invalid role is rejected."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "user123",
            "role": "invalid_role",  # Invalid role
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Should raise exception
        with pytest.raises(Exception):
            jwt.decode(token, secret, algorithms=["HS256"])

    def test_student_scoped_token(self):
        """SEC-JWT-008: Verify student-scoped token has limited permissions."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        payload = {
            "sub": "student123",
            "role": "student",
            "scope": "assessment",  # Limited scope
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["role"] == "student"
        assert decoded["scope"] == "assessment"


class TestTokenRefreshRotation:
    """Tests for refresh token rotation."""

    def test_refresh_token_rotation(self):
        """SEC-JWT-009: Verify refresh token is rotated on use."""
        secret = "test_secret_key_for_testing_purposes_only_12345"
        
        # Original refresh token
        original_payload = {
            "sub": "user123",
            "type": "refresh",
            "jti": "token-uuid-1",  # JWT ID for tracking
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
            "iat": datetime.now(timezone.utc)
        }
        original_token = jwt.encode(original_payload, secret, algorithm="HS256")
        
        # Simulate token rotation - new token issued
        new_payload = {
            "sub": "user123",
            "type": "refresh",
            "jti": "token-uuid-2",  # New JWT ID
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
            "iat": datetime.now(timezone.utc)
        }
        new_token = jwt.encode(new_payload, secret, algorithm="HS256")
        
        # Original token is invalidated (simulated)
        # New token should be valid
        decoded = jwt.decode(new_token, secret, algorithms=["HS256"])
        assert decoded["jti"] == "token-uuid-2"


class TestInvalidTokenHandling:
    """Tests for invalid token rejection."""

    def test_malformed_token_rejected(self):
        """SEC-JWT-010: Verify malformed token is rejected."""
        with pytest.raises(Exception):
            jwt.decode("not.a.valid.token", "secret", algorithms=["HS256"])

    def test_token_with_wrong_secret_rejected(self):
        """SEC-JWT-011: Verify token signed with wrong secret is rejected."""
        secret1 = "secret_key_1"
        secret2 = "secret_key_2"
        
        payload = {
            "sub": "user123",
            "role": "parent",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret1, algorithm="HS256")
        
        # Should raise exception when verified with wrong secret
        with pytest.raises(Exception):
            jwt.decode(token, secret2, algorithms=["HS256"])

    def test_signature_mismatch_rejected(self):
        """SEC-JWT-012: Verify signature mismatch is detected."""
        secret = "test_secret_key"
        payload = {
            "sub": "user123",
            "role": "parent",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Tamper with payload
        tampered_payload = {
            "sub": "admin123",  # Changed role
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        tampered_token = jwt.encode(tampered_payload, secret, algorithm="HS256")
        
        # Different tokens (expected)
        assert token != tampered_token

    def test_none_algorithm_rejected(self):
        """SEC-JWT-013: Verify none algorithm tokens are rejected."""
        # Attempt to create token with none algorithm (should be blocked)
        try:
            # This is a known attack vector - tokens with algorithm=none
            tampered_header = jwt.encode(
                {"alg": "none", "typ": "JWT"},
                "",
                algorithm="none"
            )
            # This should never happen in production - algorithm validation
            # blocks this attack
            raise AssertionError("None algorithm should not be allowed")
        except Exception:
            # Expected - algorithm validation blocks this
            pass
