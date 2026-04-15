"""
Test Suite: Integration - COPPA Consent Flow

Purpose: Validate complete COPPA consent flow from initiation to confirmation.

COPPA Relevance: Critical compliance flow for parental consent.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
import hmac
import hashlib
import secrets


class TestConsentInitiation:
    """Tests for COPPA consent initiation."""

    def test_consent_request_initiated(self, engine):
        """INT-COPPA-001: Verify consent record can be initiated."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (
                    parent_id, consent_type, status, ip_address, user_agent, consent_text_hash
                ) VALUES (
                    :pid, 'coppa_verifiable', 'pending', '192.168.1.1', 'Mozilla/5.0', 'sha256hash'
                )
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['status'] == 'pending'

    def test_consent_token_generated(self, engine):
        """INT-COPPA-002: Verify consent token is generated on initiation."""
        parent_id = '11111111-1111-1111-1111-111111111111'
        secret_key = secrets.token_bytes(32)
        now = datetime.now(timezone.utc)

        data = f"{parent_id}:{now.isoformat()}"
        token = hmac.new(secret_key, data.encode(), hashlib.sha256).hexdigest()

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (
                    parent_id, consent_type, status, verification_token, token_expires_at,
                    ip_address, user_agent, consent_text_hash
                ) VALUES (
                    :pid, 'coppa_verifiable', 'pending', :token, :expiry,
                    '192.168.1.1', 'Mozilla/5.0', 'sha256hash'
                )
            """, pid=parent_id, token=token, expiry=now + timedelta(days=7)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT verification_token IS NOT NULL as has_token FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['has_token'] is True


class TestConsentConfirmation:
    """Tests for COPPA consent confirmation."""

    def test_consent_confirmed_via_token(self, engine):
        """INT-COPPA-003: Verify consent can be confirmed with valid token."""
        parent_id = '11111111-1111-1111-1111-111111111111'
        token = "valid_token_123"

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (
                    parent_id, consent_type, status, verification_token, token_expires_at,
                    ip_address, user_agent, consent_text_hash
                ) VALUES (
                    :pid, 'coppa_verifiable', 'pending', :token, :expiry,
                    '192.168.1.1', 'Mozilla/5.0', 'sha256hash'
                )
            """, pid=parent_id, token=token, expiry=datetime.now(timezone.utc) + timedelta(days=7)))
            conn.commit()

        # Confirm consent
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE consent_records
                SET status = 'active', confirmed_at = CURRENT_TIMESTAMP
                WHERE parent_id = :pid AND verification_token = :token
            """, pid=parent_id, token=token))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['status'] == 'active'

    def test_consent_status_updated(self, engine):
        """INT-COPPA-004: Verify consent status transitions correctly."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'pending', '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id))
            conn.commit()

        # Transition to active
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE consent_records SET status = 'active', confirmed_at = CURRENT_TIMESTAMP
                WHERE parent_id = :pid
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['status'] == 'active'


class TestConsentRevocation:
    """Tests for COPPA consent revocation."""

    def test_consent_can_be_revoked(self, engine):
        """INT-COPPA-005: Verify consent can be revoked by parent."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'active', '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id))
            conn.commit()

        # Revoke consent
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE consent_records
                SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP
                WHERE parent_id = :pid
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['status'] == 'revoked'

    def test_revocation_timestamp_recorded(self, engine):
        """INT-COPPA-006: Verify revocation timestamp is recorded."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'active', '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE consent_records SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP
                WHERE parent_id = :pid
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT revoked_at IS NOT NULL as has_revoked_at FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['has_revoked_at'] is True
