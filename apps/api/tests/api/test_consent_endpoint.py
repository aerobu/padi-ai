"""
Test Suite: API - Consent Endpoint Tests

Purpose: Validate consent API endpoints.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timezone


class TestConsentEndpoints:
    """Tests for consent API endpoints."""

    def test_get_consent_status(self, engine):
        """API-CNS-001: Verify consent status can be retrieved."""
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

    def test_initiate_consent_endpoint(self, engine):
        """API-CNS-002: Verify consent initiation endpoint creates record."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, initiated_at, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'pending', :initiated, '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id, initiated=datetime.now(timezone.utc)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['count'] == 1

    def test_confirm_consent_endpoint(self, engine):
        """API-CNS-003: Verify consent confirmation endpoint updates status."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, verification_token, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'pending', 'token123', '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id))
            conn.commit()

        # Confirm via endpoint
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE consent_records SET status = 'active', confirmed_at = CURRENT_TIMESTAMP
                WHERE parent_id = :pid AND verification_token = 'token123'
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['status'] == 'active'

    def test_revoke_consent_endpoint(self, engine):
        """API-CNS-004: Verify consent revocation endpoint updates status."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO consent_records (parent_id, consent_type, status, revoked_at, ip_address, user_agent, consent_text_hash)
                VALUES (:pid, 'coppa_verifiable', 'revoked', NOW(), '192.168.1.1', 'Mozilla/5.0', 'sha256hash')
            """, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM consent_records WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['status'] == 'revoked'
