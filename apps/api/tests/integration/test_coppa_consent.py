"""Integration tests for COPPA consent flow.

This test suite validates the complete COPPA consent process:
- Token generation
- Email delivery
- Token validation
- Consent record creation
- Student access control
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import hmac
import hashlib


class TestConsentTokenGeneration:
    """Test COPPA consent token generation."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def consent_service(self, mock_db_session):
        """Create consent service."""
        from src.services.coppa_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository

        consent_repo = ConsentRepository(mock_db_session)
        return ConsentService(consent_repository=consent_repo)

    @pytest.mark.asyncio
    async def test_token_generation(self, consent_service):
        """Consent token is generated with proper format."""
        token = consent_service.generate_consent_token(parent_id="parent-123")

        # Token should have required fields
        assert "parent_id" in token
        assert "expires_at" in token
        assert "signature" in token

        # Parent ID should match
        assert token["parent_id"] == "parent-123"

        # Expires in 7 days
        expires = datetime.fromisoformat(token["expires_at"])
        assert (expires - datetime.utcnow()).days == 7

    @pytest.mark.asyncio
    async def test_token_signature_valid(self, consent_service):
        """Generated token has valid HMAC-SHA256 signature."""
        token = consent_service.generate_consent_token(parent_id="parent-123")

        # Signature should be 64 hex characters (SHA-256)
        assert len(token["signature"]) == 64

        # Verify signature
        secret = consent_service.settings.COPPA_CONSENT_SECRET
        message = f"{token['parent_id']}:{token['expires_at']}"
        expected_signature = hmac.new(
            secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        assert token["signature"] == expected_signature


class TestConsentEmailDelivery:
    """Test consent email delivery."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def consent_service(self, mock_db_session):
        """Create consent service."""
        from src.services.coppa_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository

        consent_repo = ConsentRepository(mock_db_session)
        return ConsentService(consent_repository=consent_repo)

    @pytest.mark.asyncio
    async def test_consent_email_sent(self, consent_service):
        """Consent email is sent with token."""
        # Mock email service
        with patch("src.services.email_service.send_email") as mock_send_email:
            result = await consent_service.send_consent_email(
                parent_id="parent-123",
                parent_email="parent@example.com",
                consent_token="test-token-123",
            )

            assert result["sent"] is True
            mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_consent_email_content(self, consent_service):
        """Consent email contains required content."""
        mock_consent_link = "https://padi.ai/consent?token=test-token"

        with patch("src.services.email_service.send_email") as mock_send_email:
            await consent_service.send_consent_email(
                parent_id="parent-123",
                parent_email="parent@example.com",
                consent_token="test-token-123",
            )

            # Verify email content
            call_args = mock_send_email.call_args
            assert call_args[1]["to"] == "parent@example.com"
            assert "consent" in call_args[1]["subject"].lower()
            assert mock_consent_link in call_args[1]["body"]


class TestConsentValidation:
    """Test COPPA consent token validation."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def consent_service(self, mock_db_session):
        """Create consent service."""
        from src.services.coppa_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository

        consent_repo = ConsentRepository(mock_db_session)
        return ConsentService(consent_repository=consent_repo)

    @pytest.mark.asyncio
    async def test_valid_token_accepted(self, consent_service):
        """Valid consent token is accepted."""
        # Generate valid token
        valid_token = consent_service.generate_consent_token(parent_id="parent-123")

        # Mock repository (not used)
        consent_service.consent_repository.token_already_used = MagicMock()
        consent_service.consent_repository.token_already_used.return_value = False

        result = await consent_service.validate_consent_token(
            token=valid_token,
        )

        assert result["valid"] is True
        assert result["parent_id"] == "parent-123"

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, consent_service):
        """Expired consent token is rejected."""
        # Create expired token manually
        expired_token = {
            "parent_id": "parent-123",
            "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "signature": "fake-signature",
        }

        result = await consent_service.validate_consent_token(
            token=expired_token,
        )

        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(self, consent_service):
        """Token with invalid signature is rejected."""
        invalid_token = {
            "parent_id": "parent-123",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "signature": "invalid-signature-12345",
        }

        result = await consent_service.validate_consent_token(
            token=invalid_token,
        )

        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_single_use_token(self, consent_service):
        """Consent tokens are single-use."""
        # Generate valid token
        valid_token = consent_service.generate_consent_token(parent_id="parent-123")

        # Simulate token already used
        consent_service.consent_repository.token_already_used = MagicMock()
        consent_service.consent_repository.token_already_used.return_value = True

        result = await consent_service.validate_consent_token(
            token=valid_token,
        )

        assert result["valid"] is False
        assert "already used" in result.get("error", "").lower()


class TestConsentRecordCreation:
    """Test COPPA consent record creation."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def consent_service(self, mock_db_session):
        """Create consent service."""
        from src.services.coppa_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository

        consent_repo = ConsentRepository(mock_db_session)
        return ConsentService(consent_repository=consent_repo)

    @pytest.mark.asyncio
    async def test_consent_granted_record_created(self, consent_service):
        """Consent granted creates record in database."""
        mock_consent_record = MagicMock()
        mock_consent_record.id = "consent-123"
        mock_consent_record.parent_id = "parent-123"
        mock_consent_record.consent_status = "granted"

        consent_service.consent_repository.create_record = MagicMock()
        consent_service.consent_repository.create_record.return_value = mock_consent_record

        result = await consent_service.process_consent(
            token={"parent_id": "parent-123", "signature": "valid"},
            consent_status="granted",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert result["status"] == "granted"
        assert result["record_id"] == "consent-123"
        consent_service.consent_repository.create_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_consent_denied_record_created(self, consent_service):
        """Consent denied creates record in database."""
        mock_consent_record = MagicMock()
        mock_consent_record.id = "consent-123"
        mock_consent_record.parent_id = "parent-123"
        mock_consent_record.consent_status = "denied"

        consent_service.consent_repository.create_record = MagicMock()
        consent_service.consent_repository.create_record.return_value = mock_consent_record

        result = await consent_service.process_consent(
            token={"parent_id": "parent-123", "signature": "valid"},
            consent_status="denied",
        )

        assert result["status"] == "denied"
        consent_service.consent_repository.create_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_consent_ip_hashed(self, consent_service):
        """IP address is hashed before storage."""
        mock_consent_record = MagicMock()
        mock_consent_record.id = "consent-123"

        consent_service.consent_repository.create_record = MagicMock()
        consent_service.consent_repository.create_record.return_value = mock_consent_record

        await consent_service.process_consent(
            token={"parent_id": "parent-123", "signature": "valid"},
            consent_status="granted",
            ip_address="192.168.1.1",
        )

        # Verify IP was hashed in call
        call_args = consent_service.consent_repository.create_record.call_args
        assert "ip_address_hash" in call_args.kwargs or "ip_address_hash" in call_args.args[1]

    @pytest.mark.asyncio
    async def test_consent_user_agent_hashed(self, consent_service):
        """User agent is hashed before storage."""
        mock_consent_record = MagicMock()
        mock_consent_record.id = "consent-123"

        consent_service.consent_repository.create_record = MagicMock()
        consent_service.consent_repository.create_record.return_value = mock_consent_record

        await consent_service.process_consent(
            token={"parent_id": "parent-123", "signature": "valid"},
            consent_status="granted",
            user_agent="Mozilla/5.0",
        )

        # Verify user agent was hashed in call
        call_args = consent_service.consent_repository.create_record.call_args
        assert "user_agent_hash" in call_args.kwargs or "user_agent_hash" in call_args.args[1]


class TestConsentAccessControl:
    """Test consent-based access control."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def consent_service(self, mock_db_session):
        """Create consent service."""
        from src.services.coppa_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository

        consent_repo = ConsentRepository(mock_db_session)
        return ConsentService(consent_repository=consent_repo)

    @pytest.mark.asyncio
    async def test_granted_consent_enables_access(self, consent_service):
        """Granted consent enables student access."""
        consent_service.consent_repository.has_active_consent = MagicMock()
        consent_service.consent_repository.has_active_consent.return_value = True

        can_access = await consent_service.check_access(student_id="student-123")

        assert can_access is True

    @pytest.mark.asyncio
    async def test_denied_consent_blocks_access(self, consent_service):
        """Denied consent blocks student access."""
        consent_service.consent_repository.has_active_consent = MagicMock()
        consent_service.consent_repository.has_active_consent.return_value = False

        can_access = await consent_service.check_access(student_id="student-123")

        assert can_access is False

    @pytest.mark.asyncio
    async def test_no_consent_blocks_access(self, consent_service):
        """No consent record blocks student access."""
        consent_service.consent_repository.has_active_consent = MagicMock()
        consent_service.consent_repository.has_active_consent.return_value = False

        can_access = await consent_service.check_access(student_id="student-123")

        assert can_access is False


class TestFullConsentFlow:
    """Integration test for complete COPPA consent flow."""

    @pytest.mark.asyncio
    async def test_complete_consent_flow(self):
        """Complete flow: token generation -> email -> validation -> record."""
        from src.services.coppa_service import ConsentService
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock session
        mock_session = MagicMock(spec=AsyncSession)

        # Create service
        consent_repo = ConsentRepository(mock_session)
        consent_service = ConsentService(consent_repository=consent_repo)

        # Step 1: Generate token
        token = consent_service.generate_consent_token(parent_id="parent-123")
        assert "signature" in token
        assert token["parent_id"] == "parent-123"

        # Step 2: Send email (mocked)
        with patch("src.services.email_service.send_email") as mock_send_email:
            email_result = await consent_service.send_consent_email(
                parent_id="parent-123",
                parent_email="parent@example.com",
                consent_token=token["signature"],
            )
            assert email_result["sent"] is True

        # Step 3: Validate token
        consent_service.consent_repository.token_already_used = MagicMock()
        consent_service.consent_repository.token_already_used.return_value = False

        validation_result = await consent_service.validate_consent_token(token=token)
        assert validation_result["valid"] is True

        # Step 4: Process consent (granted)
        mock_record = MagicMock()
        mock_record.id = "consent-123"

        consent_service.consent_repository.create_record = MagicMock()
        consent_service.consent_repository.create_record.return_value = mock_record

        process_result = await consent_service.process_consent(
            token=token,
            consent_status="granted",
        )

        assert process_result["status"] == "granted"
        assert process_result["record_id"] == "consent-123"

        # Step 5: Verify access
        consent_service.consent_repository.has_active_consent = MagicMock()
        consent_service.consent_repository.has_active_consent.return_value = True

        can_access = await consent_service.check_access(student_id="student-123")
        assert can_access is True
