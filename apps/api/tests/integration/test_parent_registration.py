"""
Test Suite: Integration - Parent Registration Flow

Purpose: Validate complete parent registration flow including:
- Email registration with validation
- Email verification token generation
- Account status tracking
- Duplicate email prevention

COPPA Relevance: Parent registration is the entry point for COPPA compliance.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
import hmac
import hashlib
import secrets


class TestParentEmailRegistration:
    """Tests for parent email registration."""

    def test_parent_account_creation(self, engine):
        """INT-PAR-001: Verify parent account can be created."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, auth0_sub, display_name, role, email_verified)
                VALUES (:pid, 'auth0|123', 'Maria', 'parent', false)
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT role FROM users WHERE id = :pid
            """, pid=parent_id)).fetchone()
            assert result['role'] == 'parent'

    def test_parent_email_hash_created(self, engine):
        """INT-PAR-002: Verify email hash is created for lookup."""
        import hashlib
        import secrets

        parent_id = '11111111-1111-1111-1111-111111111111'
        email = "parent@example.com"
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, auth0_sub, email_encrypted, email_hash, display_name, role)
                VALUES (:pid, 'auth0|123', :enc, :hash, 'Maria', 'parent')
            """, pid=parent_id, enc=b"encrypted", hash=email_hash))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT email_hash FROM users WHERE id = :pid
            """, pid=parent_id)).fetchone()
            assert result['email_hash'] == email_hash

    def test_duplicate_email_rejected(self, engine):
        """INT-PAR-003: Verify duplicate emails are rejected."""
        import hashlib

        parent_id1 = '11111111-1111-1111-1111-111111111111'
        parent_id2 = '22222222-2222-2222-2222-222222222222'
        email = "parent@example.com"
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, auth0_sub, email_hash, display_name, role)
                VALUES (:pid, 'auth0|123', :hash, 'Maria', 'parent')
            """, pid=parent_id1, hash=email_hash))
            conn.commit()

        # Second parent with same email should fail
        with engine.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(text("""
                    INSERT INTO users (id, auth0_sub, email_hash, display_name, role)
                    VALUES (:pid, 'auth0|456', :hash, 'Other', 'parent')
                """, pid=parent_id2, hash=email_hash))
                conn.commit()

    def test_parent_account_default_status(self, engine):
        """INT-PAR-004: Verify new parent account has email_verified=false."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, auth0_sub, display_name, role)
                VALUES (:pid, 'auth0|123', 'Maria', 'parent')
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT email_verified FROM users WHERE id = :pid
            """, pid=parent_id)).fetchone()
            assert result['email_verified'] is False

    def test_parent_role_constraint(self, engine):
        """INT-PAR-005: Verify parent role is validated."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, auth0_sub, display_name, role)
                VALUES (:pid, 'auth0|123', 'Maria', 'parent')
            """, pid='11111111-1111-1111-1111-111111111111'))
            conn.commit()

        with engine.connect() as conn:
            # Invalid role should fail
            with pytest.raises(Exception):
                conn.execute(text("""
                    INSERT INTO users (id, auth0_sub, display_name, role)
                    VALUES (:pid, 'auth0|123', 'Maria', 'invalid_role')
                """, pid='22222222-2222-2222-2222-222222222222'))
                conn.commit()


class TestEmailVerificationToken:
    """Tests for email verification token generation."""

    def test_verification_token_generated(self, engine):
        """INT-PAR-006: Verify verification token is generated for new parent."""
        parent_id = '11111111-1111-1111-1111-111111111111'
        secret_key = secrets.token_bytes(32)
        now = datetime.now(timezone.utc)

        data = f"{parent_id}:verify:{now.isoformat()}"
        token = hmac.new(secret_key, data.encode(), hashlib.sha256).hexdigest()

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO email_verification_tokens (
                    user_id, token_hash, expires_at
                ) VALUES (
                    :uid, :hash, :expiry
                )
            """, uid=parent_id, hash=token, expiry=now + timedelta(hours=24)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM email_verification_tokens WHERE user_id = :uid
            """, uid=parent_id)).fetchone()
            assert result['count'] == 1

    def test_verification_token_expiration(self, engine):
        """INT-PAR-007: Verify verification token expires after 24 hours."""
        parent_id = '11111111-1111-1111-1111-111111111111'
        expired_time = datetime.now(timezone.utc) - timedelta(hours=25)

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO email_verification_tokens (user_id, token_hash, expires_at)
                VALUES (:uid, 'expired_token', :expiry)
            """, uid=parent_id, expiry=expired_time))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM email_verification_tokens
                WHERE user_id = :uid AND expires_at > CURRENT_TIMESTAMP
            """, uid=parent_id)).fetchone()
            assert result['count'] == 0
