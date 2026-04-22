"""
Tests for Consent API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock
from src.models.models import ConsentRecord, ConsentStatus, User

@pytest.mark.asyncio
class TestConsentEndpoints:
    """Tests for consent API endpoints."""

    async def _seed_parent(self, async_db_session):
        parent = User(
            id="test-parent-id",
            auth0_id="auth0|test-parent",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True
        )
        parent.set_email("parent@example.com")
        async_db_session.add(parent)
        await async_db_session.flush()
        return parent

    async def test_get_consent_status_empty(self, client, async_db_session):
        """API-CNS-001: Verify consent status is empty when no record exists."""
        await self._seed_parent(async_db_session)
        await async_db_session.commit()
        
        response = await client.get("/api/v1/consent/status")
        assert response.status_code == 200
        data = response.json()
        assert data["has_active_consent"] is False
        assert data["consent_records"] == []

    async def test_initiate_consent(self, client, async_db_session):
        """API-CNS-002: Verify consent initiation creates a pending record."""
        await self._seed_parent(async_db_session)
        await async_db_session.commit()
        
        payload = {
            "student_display_name": "Junior",
            "acknowledgements": [
                "data_collection",
                "data_use",
                "third_party_disclosure",
                "parental_rights"
            ]
        }
        
        response = await client.post("/api/v1/consent/initiate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "consent_id" in data

    async def test_confirm_consent(self, client, async_db_session, mock_redis_client):
        """API-CNS-003: Verify consent confirmation updates status."""
        await self._seed_parent(async_db_session)
        
        from src.repositories.consent_repository import ConsentRepository
        repo = ConsentRepository(async_db_session)
        
        # Create a pending record manually
        token = "test-token" * 10 # Must be 64-256 chars
        record = await repo.create_pending_consent(
            user_id="test-parent-id",
            student_id=None,
            consent_type="coppa_verifiable",
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )
        await async_db_session.commit()
        
        # Mock Redis returning the token data
        mock_redis_client.get.return_value = {
            "user_id": "test-parent-id",
            "student_name": "Junior",
            "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat()
        }
        
        response = await client.post("/api/v1/consent/confirm", json={"token": token})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        
        # Verify status in DB
        updated_record = await repo.get_by_id(record.id)
        assert updated_record.status == ConsentStatus.GRANTED

    async def test_get_consent_status_active(self, client, async_db_session):
        """API-CNS-004: Verify active consent status is reported correctly."""
        await self._seed_parent(async_db_session)
        
        from src.repositories.consent_repository import ConsentRepository
        repo = ConsentRepository(async_db_session)
        
        # Create an active record
        token = "test-token" * 10
        record = await repo.create_pending_consent(
            user_id="test-parent-id",
            student_id=None,
            consent_type="coppa_verifiable",
            token=token,
            expires_at=datetime.utcnow()
        )
        await repo.confirm_consent(record.id, datetime.utcnow())
        await async_db_session.commit()
        
        response = await client.get("/api/v1/consent/status")
        assert response.status_code == 200
        data = response.json()
        assert data["has_active_consent"] is True
        assert len(data["consent_records"]) == 1
        assert data["consent_records"][0]["status"] == "active"
