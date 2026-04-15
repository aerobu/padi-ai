"""Tests for COPPA consent service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestConsentServiceInitialization:
    """Test ConsentService initialization."""

    def test_consent_service_initialization(self):
        """ConsentService initializes with repository and redis client."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock session
        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)

        service = ConsentService(consent_repository=repository)

        assert service.consent_repository == repository
        assert service.redis_client is not None
        assert service.TOKEN_EXPIRY_HOURS == 48


class TestConsentServiceInitiateConsent:
    """Test ConsentService.initiate_consent method."""

    @pytest.mark.asyncio
    async def test_initiate_consent_creates_pending_record(self):
        """initiate_consent creates pending consent record."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        mock_record = MagicMock()
        mock_record.id = "consent-123"

        repository = ConsentRepository(mock_session)
        repository.create_pending_consent = MagicMock()
        repository.create_pending_consent.return_value = mock_record

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()

        result = await service.initiate_consent(
            user_id="user-123",
            student_display_name="Test Student",
            acknowledgements=["data_collection", "data_use", "third_party_disclosure", "parental_rights"],
            ip_address="192.168.1.1",
            email="parent@example.com",
        )

        assert result["consent_id"] == "consent-123"
        assert result["status"] == "pending"
        assert result["verification_method"] == "email_plus"
        assert "email_sent_to" in result
        assert "expires_at" in result

    @pytest.mark.asyncio
    async def test_initiate_consent_requires_all_acknowledgements(self):
        """initiate_consent requires all required acknowledgements."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)
        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()

        # Missing one acknowledgement
        with pytest.raises(ValueError, match="All required consent clauses"):
            await service.initiate_consent(
                user_id="user-123",
                student_display_name="Test Student",
                acknowledgements=["data_collection", "data_use"],  # Missing two
                ip_address="192.168.1.1",
                email="parent@example.com",
            )

    @pytest.mark.asyncio
    async def test_initiate_consent_requires_existing_user(self):
        """initiate_consent requires existing user."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)
        repository.get_active_consent_for_user = MagicMock()
        repository.get_active_consent_for_user.return_value = MagicMock()  # Already has consent

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()

        with pytest.raises(ValueError, match="Active consent already exists"):
            await service.initiate_consent(
                user_id="user-123",
                student_display_name="Test Student",
                acknowledgements=["data_collection", "data_use", "third_party_disclosure", "parental_rights"],
                ip_address="192.168.1.1",
                email="parent@example.com",
            )

    @pytest.mark.asyncio
    async def test_initiate_consent_generates_token(self):
        """initiate_consent generates unique token."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        mock_record = MagicMock()
        mock_record.id = "consent-123"

        repository = ConsentRepository(mock_session)
        repository.create_pending_consent = MagicMock()
        repository.create_pending_consent.return_value = mock_record

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()

        result1 = await service.initiate_consent(
            user_id="user-123",
            student_display_name="Test Student",
            acknowledgements=["data_collection", "data_use", "third_party_disclosure", "parental_rights"],
            ip_address="192.168.1.1",
            email="parent@example.com",
        )

        result2 = await service.initiate_consent(
            user_id="user-456",
            student_display_name="Another Student",
            acknowledgements=["data_collection", "data_use", "third_party_disclosure", "parental_rights"],
            ip_address="192.168.1.2",
            email="another@example.com",
        )

        # Both should have tokens (though we can't verify uniqueness in this test)
        assert result1["verification_token"] is not None
        assert result2["verification_token"] is not None
        assert len(result1["verification_token"]) == 64  # 32 bytes hex

    @pytest.mark.asyncio
    async def test_initiate_consent_sets_redis_token(self):
        """initiate_consent stores token in Redis."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        mock_record = MagicMock()
        mock_record.id = "consent-123"

        repository = ConsentRepository(mock_session)
        repository.create_pending_consent = MagicMock()
        repository.create_pending_consent.return_value = mock_record

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()

        await service.initiate_consent(
            user_id="user-123",
            student_display_name="Test Student",
            acknowledgements=["data_collection", "data_use", "third_party_disclosure", "parental_rights"],
            ip_address="192.168.1.1",
            email="parent@example.com",
        )

        # Should have called set on redis client
        service.redis_client.set.assert_called()


class TestConsentServiceConfirmConsent:
    """Test ConsentService.confirm_consent method."""

    @pytest.mark.asyncio
    async def test_confirm_consent_valid_token(self):
        """confirm_consent confirms valid token."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        mock_record = MagicMock()
        mock_record.id = "consent-123"
        mock_record.user_id = "user-123"

        repository = ConsentRepository(mock_session)
        repository.get_pending_by_token = MagicMock()
        repository.get_pending_by_token.return_value = mock_record
        repository.confirm_consent = MagicMock()
        repository.confirm_consent.return_value = mock_record

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()
        service.redis_client.get = MagicMock()
        service.redis_client.get.return_value = {
            "user_id": "user-123",
            "student_name": "Test Student",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

        result = await service.confirm_consent(token="valid-token-123")

        assert result["status"] == "active"
        assert result["consent_id"] == "consent-123"
        assert "confirmed_at" in result
        assert "expires_at" in result

    @pytest.mark.asyncio
    async def test_confirm_consent_invalid_token(self):
        """confirm_consent rejects invalid token."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()
        service.redis_client.get = MagicMock()
        service.redis_client.get.return_value = None  # Token not found

        with pytest.raises(ValueError, match="Invalid or expired consent token"):
            await service.confirm_consent(token="invalid-token")

    @pytest.mark.asyncio
    async def test_confirm_consent_expired_token(self):
        """confirm_consent rejects expired token."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        mock_record = MagicMock()

        repository = ConsentRepository(mock_session)

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()
        service.redis_client.get = MagicMock()
        service.redis_client.get.return_value = {
            "user_id": "user-123",
            "student_name": "Test Student",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),  # Expired
        }

        with pytest.raises(ValueError, match="Consent token has expired"):
            await service.confirm_consent(token="expired-token")

    @pytest.mark.asyncio
    async def test_confirm_consent_missing_record(self):
        """confirm_consent rejects token with no record."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)
        repository.get_pending_by_token = MagicMock()
        repository.get_pending_by_token.return_value = None

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()
        service.redis_client.get = MagicMock()
        service.redis_client.get.return_value = {
            "user_id": "user-123",
            "student_name": "Test Student",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

        with pytest.raises(ValueError, match="Consent record not found"):
            await service.confirm_consent(token="token-without-record")


class TestConsentServiceVerifyActiveConsent:
    """Test ConsentService.verify_active_consent method."""

    @pytest.mark.asyncio
    async def test_verify_active_consent_redis_fallback(self):
        """verify_active_consent checks Redis first."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()
        service.redis_client.get_active_consent = MagicMock()
        service.redis_client.get_active_consent.return_value = True

        result = await service.verify_active_consent("user-123")

        assert result is True
        service.redis_client.get_active_consent.assert_called_once_with("user-123")
        # Should not call repository if Redis says yes
        repository.has_active_consent.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_active_consent_db_fallback(self):
        """verify_active_consent falls back to database."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()
        service.redis_client.get_active_consent = MagicMock()
        service.redis_client.get_active_consent.return_value = None  # Redis miss

        repository.has_active_consent = MagicMock()
        repository.has_active_consent.return_value = True

        result = await service.verify_active_consent("user-123")

        assert result is True
        repository.has_active_consent.assert_called_once_with("user-123")


class TestConsentServiceGetConsentStatus:
    """Test ConsentService.get_consent_status method."""

    @pytest.mark.asyncio
    async def test_get_consent_status_returns_summary(self):
        """get_consent_status returns consent summary."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)

        # Create mock records
        mock_record1 = MagicMock()
        mock_record1.id = "consent-123"
        mock_record1.consent_type = "coppa_verifiable"
        mock_record1.status = "granted"
        mock_record1.created_at = datetime.utcnow()
        mock_record1.consented_at = datetime.utcnow()
        mock_record1.metadata_json = None

        repository = ConsentRepository(mock_session)
        repository.get_consent_status = MagicMock()
        repository.get_consent_status.return_value = [mock_record1]

        service = ConsentService(consent_repository=repository)

        result = await service.get_consent_status("user-123")

        assert "has_active_consent" in result
        assert "consent_records" in result
        assert result["has_active_consent"] is True
        assert len(result["consent_records"]) == 1

    @pytest.mark.asyncio
    async def test_get_consent_status_no_consent(self):
        """get_consent_status returns no consent when none exists."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)

        repository = ConsentRepository(mock_session)
        repository.get_consent_status = MagicMock()
        repository.get_consent_status.return_value = []

        service = ConsentService(consent_repository=repository)

        result = await service.get_consent_status("user-123")

        assert result["has_active_consent"] is False
        assert len(result["consent_records"]) == 0


class TestConsentServiceRevokeConsent:
    """Test ConsentService.revoke_consent method."""

    @pytest.mark.asyncio
    async def test_revoke_consent_success(self):
        """revoke_consent revokes consent and updates Redis."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        mock_record = MagicMock()
        mock_record.id = "consent-123"
        mock_record.user_id = "user-123"

        repository = ConsentRepository(mock_session)
        repository.revoke_consent = MagicMock()
        repository.revoke_consent.return_value = mock_record

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()

        result = await service.revoke_consent("consent-123")

        assert result is not None
        assert result.id == "consent-123"
        service.redis_client.revoke_active_consent.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_revoke_consent_not_found(self):
        """revoke_consent returns None for missing consent."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)

        repository = ConsentRepository(mock_session)
        repository.revoke_consent = MagicMock()
        repository.revoke_consent.return_value = None

        service = ConsentService(consent_repository=repository)
        service.redis_client = MagicMock()

        result = await service.revoke_consent("missing-consent")

        assert result is None
        # Should not call Redis if consent not found
        service.redis_client.revoke_active_consent.assert_not_called()


class TestConsentServiceMaskEmail:
    """Test ConsentService._mask_email method."""

    def test_mask_email_masks_local_part(self):
        """_mask_email masks local part of email."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)
        service = ConsentService(consent_repository=repository)

        masked = service._mask_email("john.doe@gmail.com")

        assert masked.startswith("j")
        assert "@gmail.com" in masked
        assert "*" in masked

    def test_mask_email_preserves_domain(self):
        """_mask_email preserves email domain."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)
        service = ConsentService(consent_repository=repository)

        masked = service._mask_email("user@company.org")

        assert "@company.org" in masked

    def test_mask_email_short_local(self):
        """_mask_email handles short local part."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)
        service = ConsentService(consent_repository=repository)

        masked = service._mask_email("a@b.com")

        assert masked.startswith("a")
        assert "@b.com" in masked

    def test_mask_email_invalid_email(self):
        """_mask_email returns invalid email unchanged."""
        from src.services.consent_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)
        service = ConsentService(consent_repository=repository)

        masked = service._mask_email("not-an-email")

        assert masked == "not-an-email"


class TestGetConsentService:
    """Test singleton consent service accessor."""

    def test_get_consent_service_raises_not_initialized(self):
        """get_consent_service raises error if not initialized."""
        from src.services.consent_service import get_consent_service

        with pytest.raises(RuntimeError, match="ConsentService not initialized"):
            get_consent_service()

    def test_initialize_consent_service(self):
        """initialize_consent_service creates and returns service."""
        from src.services.consent_service import (
            initialize_consent_service,
            ConsentService,
        )
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)
        repository = ConsentRepository(mock_session)

        service = initialize_consent_service(consent_repository=repository)

        assert isinstance(service, ConsentService)
