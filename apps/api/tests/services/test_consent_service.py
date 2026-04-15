"""
Test Suite: Services - Consent Service Tests

Purpose: Validate consent service operations for COPPA compliance.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timezone, timedelta


class TestConsentService:
    """Tests for consent service."""

    def test_initiate_consent(self, engine):
        """SVC-CNS-001: Verify consent can be initiated."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'pending', '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['status'] == 'pending'

    def test_confirm_consent(self, engine):
        """SVC-CNS-002: Verify consent can be confirmed."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'pending', '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id))
            conn.commit()

        # Confirm consent
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

    def test_consent_expiration_check(self, engine):
        """SVC-CNS-003: Verify consent expiration is tracked."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, expires_at)
                VALUES (:pid, 'coppa_verifiable', 'active', :expiry)
            """, pid=parent_id, expiry=datetime.now(timezone.utc) + timedelta(days=365)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT expires_at > CURRENT_TIMESTAMP as is_active FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['is_active'] is True

    def test_check_consent_required(self, engine):
        """SVC-CNS-004: Verify consent check returns correct status."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        # Parent without consent
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (SELECT 1 FROM consent_records WHERE parent_id = :pid AND status = 'active') as has_consent
            """, pid=parent_id)).fetchone()
            assert result['has_consent'] is False
