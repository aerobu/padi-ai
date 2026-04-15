"""Integration tests for parent registration flow.

This test suite validates the complete parent registration process:
- Parent account creation
- Email verification
- Child account creation
- Parent-child link establishment
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


class TestParentRegistration:
    """Test parent registration endpoint integration."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def parent_registration_service(self, mock_db_session):
        """Create parent registration service."""
        from src.services.parent_service import ParentRegistrationService
        from src.repositories.parent_repository import ParentRepository

        parent_repo = ParentRepository(mock_db_session)
        return ParentRegistrationService(parent_repository=parent_repo)

    @pytest.mark.asyncio
    async def test_parent_registration_success(self, parent_registration_service):
        """Parent registration creates account and sends verification email."""
        # Mock repository
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"
        mock_parent.email = "parent@example.com"

        parent_registration_service.parent_repository.create = MagicMock()
        parent_registration_service.parent_repository.create.return_value = mock_parent

        # Mock email sending
        with patch("src.services.email_service.send_email") as mock_send_email:
            result = await parent_registration_service.register_parent(
                email="parent@example.com",
                display_name="Test Parent",
            )

            assert result["parent_id"] == "parent-123"
            assert result["status"] == "pending_verification"
            mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_parent_registration_duplicate_email(self, parent_registration_service):
        """Parent registration rejects duplicate email."""
        # Mock repository - email exists
        parent_registration_service.parent_repository.get_by_email = MagicMock()
        parent_registration_service.parent_repository.get_by_email.return_value = MagicMock()

        with pytest.raises(ValueError, match="Email already registered"):
            await parent_registration_service.register_parent(
                email="parent@example.com",
                display_name="Test Parent",
            )

    @pytest.mark.asyncio
    async def test_parent_registration_invalid_email(self, parent_registration_service):
        """Parent registration rejects invalid email."""
        with pytest.raises(ValueError, match="Invalid email address"):
            await parent_registration_service.register_parent(
                email="invalid-email",
                display_name="Test Parent",
            )


class TestEmailVerification:
    """Test email verification during parent registration."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def email_verification_service(self, mock_db_session):
        """Create email verification service."""
        from src.services.email_verification_service import EmailVerificationService
        from src.repositories.parent_repository import ParentRepository

        parent_repo = ParentRepository(mock_db_session)
        return EmailVerificationService(parent_repository=parent_repo)

    @pytest.mark.asyncio
    async def test_verify_email_success(self, email_verification_service):
        """Email verification marks parent email as verified."""
        # Mock parent
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"
        mock_parent.email_verified = False

        email_verification_service.parent_repository.get_by_email = MagicMock()
        email_verification_service.parent_repository.get_by_email.return_value = mock_parent

        result = await email_verification_service.verify_email(
            email="parent@example.com",
            verification_token="valid-token-123",
        )

        assert result["verified"] is True
        assert mock_parent.email_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_expired_token(self, email_verification_service):
        """Email verification rejects expired token."""
        # Mock parent with expired token
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"
        mock_parent.verification_token_expires_at = datetime.utcnow() - timedelta(days=1)

        email_verification_service.parent_repository.get_by_email = MagicMock()
        email_verification_service.parent_repository.get_by_email.return_value = mock_parent

        with pytest.raises(ValueError, match="Verification token expired"):
            await email_verification_service.verify_email(
                email="parent@example.com",
                verification_token="expired-token",
            )

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, email_verification_service):
        """Email verification rejects invalid token."""
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"
        mock_parent.verification_token = "stored-token"

        email_verification_service.parent_repository.get_by_email = MagicMock()
        email_verification_service.parent_repository.get_by_email.return_value = mock_parent

        with pytest.raises(ValueError, match="Invalid verification token"):
            await email_verification_service.verify_email(
                email="parent@example.com",
                verification_token="wrong-token",
            )


class TestChildAccountCreation:
    """Test child account creation by verified parent."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def child_creation_service(self, mock_db_session):
        """Create child account creation service."""
        from src.services.child_service import ChildAccountService
        from src.repositories.child_repository import ChildRepository
        from src.repositories.parent_repository import ParentRepository

        child_repo = ChildRepository(mock_db_session)
        parent_repo = ParentRepository(mock_db_session)

        return ChildAccountService(
            child_repository=child_repo,
            parent_repository=parent_repo,
        )

    @pytest.mark.asyncio
    async def test_create_child_success(self, child_creation_service):
        """Verified parent can create child account."""
        # Mock parent (verified)
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"
        mock_parent.email_verified = True

        child_creation_service.parent_repository.get_by_id = MagicMock()
        child_creation_service.parent_repository.get_by_id.return_value = mock_parent

        # Mock child creation
        mock_child = MagicMock()
        mock_child.id = "student-456"
        mock_child.parent_id = "parent-123"

        child_creation_service.child_repository.create = MagicMock()
        child_creation_service.child_repository.create.return_value = mock_child

        result = await child_creation_service.create_child_account(
            parent_id="parent-123",
            grade_level=4,
            display_name="John",
        )

        assert result["student_id"] == "student-456"
        assert result["parent_id"] == "parent-123"

    @pytest.mark.asyncio
    async def test_create_child_unverified_parent(self, child_creation_service):
        """Unverified parent cannot create child account."""
        # Mock parent (not verified)
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"
        mock_parent.email_verified = False

        child_creation_service.parent_repository.get_by_id = MagicMock()
        child_creation_service.parent_repository.get_by_id.return_value = mock_parent

        with pytest.raises(ValueError, match="Parent email must be verified"):
            await child_creation_service.create_child_account(
                parent_id="parent-123",
                grade_level=4,
                display_name="John",
            )


class TestParentChildLink:
    """Test parent-child link establishment."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def link_service(self, mock_db_session):
        """Create link service."""
        from src.services.link_service import ParentChildLinkService
        from src.repositories.link_repository import ParentChildLinkRepository

        link_repo = ParentChildLinkRepository(mock_db_session)
        return ParentChildLinkService(link_repository=link_repo)

    @pytest.mark.asyncio
    async def test_create_link_success(self, link_service):
        """Parent-child link is created successfully."""
        # Mock parent and child
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"

        mock_child = MagicMock()
        mock_child.id = "student-456"

        link_service.parent_repository.get_by_id = MagicMock()
        link_service.parent_repository.get_by_id.return_value = mock_parent

        link_service.child_repository.get_by_id = MagicMock()
        link_service.child_repository.get_by_id.return_value = mock_child

        mock_link = MagicMock()
        mock_link.id = "link-789"
        mock_link.parent_id = "parent-123"
        mock_link.student_id = "student-456"

        link_service.link_repository.create = MagicMock()
        link_service.link_repository.create.return_value = mock_link

        result = await link_service.create_link(
            parent_id="parent-123",
            student_id="student-456",
        )

        assert result["link_id"] == "link-789"
        assert result["parent_id"] == "parent-123"
        assert result["student_id"] == "student-456"

    @pytest.mark.asyncio
    async def test_create_link_duplicate(self, link_service):
        """Parent-child link creation rejects existing link."""
        link_service.link_repository.get_by_parent_student = MagicMock()
        link_service.link_repository.get_by_parent_student.return_value = MagicMock()

        with pytest.raises(ValueError, match="Link already exists"):
            await link_service.create_link(
                parent_id="parent-123",
                student_id="student-456",
            )

    @pytest.mark.asyncio
    async def test_link_token_generation(self, link_service):
        """Link token is generated for parent-child connection."""
        # Mock parent and child
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"

        mock_child = MagicMock()
        mock_child.id = "student-456"

        link_service.parent_repository.get_by_id = MagicMock()
        link_service.parent_repository.get_by_id.return_value = mock_parent

        link_service.child_repository.get_by_id = MagicMock()
        link_service.child_repository.get_by_id.return_value = mock_child

        mock_link = MagicMock()
        mock_link.link_token = "link-token-123"

        link_service.link_repository.create = MagicMock()
        link_service.link_repository.create.return_value = mock_link

        result = await link_service.create_link(
            parent_id="parent-123",
            student_id="student-456",
        )

        assert result["link_token"] == "link-token-123"
        assert result["link_token"] is not None


class TestFullRegistrationFlow:
    """Integration test for complete parent registration flow."""

    @pytest.mark.asyncio
    async def test_complete_registration_to_child_creation(self):
        """Complete flow: register parent -> verify email -> create child."""
        from src.services.parent_service import ParentRegistrationService
        from src.services.email_verification_service import EmailVerificationService
        from src.services.child_service import ChildAccountService
        from src.repositories.parent_repository import ParentRepository
        from src.repositories.child_repository import ChildRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock session
        mock_session = MagicMock(spec=AsyncSession)

        # Create services
        parent_repo = ParentRepository(mock_session)
        child_repo = ChildRepository(mock_session)

        parent_service = ParentRegistrationService(parent_repository=parent_repo)
        email_service = EmailVerificationService(parent_repository=parent_repo)
        child_service = ChildAccountService(
            child_repository=child_repo,
            parent_repository=parent_repo,
        )

        # Step 1: Register parent
        with patch("src.services.email_service.send_email"):
            registration_result = await parent_service.register_parent(
                email="parent@example.com",
                display_name="Test Parent",
            )

        assert registration_result["status"] == "pending_verification"

        # Step 2: Verify email
        mock_parent = MagicMock()
        mock_parent.id = "parent-123"
        mock_parent.email_verified = False
        mock_parent.verification_token = "valid-token"
        mock_parent.verification_token_expires_at = datetime.utcnow() + timedelta(days=1)

        parent_repo.get_by_email = MagicMock()
        parent_repo.get_by_email.return_value = mock_parent

        verification_result = await email_service.verify_email(
            email="parent@example.com",
            verification_token="valid-token",
        )

        assert verification_result["verified"] is True
        assert mock_parent.email_verified is True

        # Step 3: Create child
        mock_child = MagicMock()
        mock_child.id = "student-456"

        child_repo.create = MagicMock()
        child_repo.create.return_value = mock_child

        child_result = await child_service.create_child_account(
            parent_id="parent-123",
            grade_level=4,
            display_name="John",
        )

        assert child_result["student_id"] == "student-456"
        assert child_result["parent_id"] == "parent-123"
