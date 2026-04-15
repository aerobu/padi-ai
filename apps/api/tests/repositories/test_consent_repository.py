"""Tests for consent repository."""

import pytest
from datetime import datetime


class TestConsentRepository:
    """Test ConsentRepository."""

    @pytest.fixture
    def repository(self, session):
        """Create ConsentRepository for tests."""
        from src.repositories.consent_repository import ConsentRepository

        return ConsentRepository(session)

    def test_get_active_consent_for_user(self, repository, user):
        """get_active_consent_for_user returns active consent."""
        from src.models.models import ConsentRecord, ConsentStatus

        # Create active consent
        active_consent = ConsentRecord(
            id="consent-active",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.GRANTED,
            consented_at=datetime.utcnow(),
        )
        repository.session.add(active_consent)

        # Create revoked consent
        revoked_consent = ConsentRecord(
            id="consent-revoked",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.REVOKED,
        )
        repository.session.add(revoked_consent)
        repository.session.commit()

        result = repository.get_active_consent_for_user(user.id)

        assert result is not None
        assert result.id == "consent-active"
        assert result.status == ConsentStatus.GRANTED

    def test_get_active_consent_for_user_none(self, repository, user):
        """get_active_consent_for_user returns None when no consent."""
        result = repository.get_active_consent_for_user(user.id)
        assert result is None

    def test_has_active_consent(self, repository, user):
        """has_active_consent returns True for granted consent."""
        from src.models.models import ConsentRecord, ConsentStatus

        consent = ConsentRecord(
            id="consent-1",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.GRANTED,
            consented_at=datetime.utcnow(),
        )
        repository.session.add(consent)
        repository.session.commit()

        result = repository.has_active_consent(user.id)

        assert result is True

    def test_has_active_consent_pending(self, repository, user):
        """has_active_consent returns False for pending consent."""
        from src.models.models import ConsentRecord, ConsentStatus

        consent = ConsentRecord(
            id="consent-1",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.PENDING,
        )
        repository.session.add(consent)
        repository.session.commit()

        result = repository.has_active_consent(user.id)

        assert result is False

    def test_has_active_consent_none(self, repository, user):
        """has_active_consent returns False when no consent."""
        result = repository.has_active_consent(user.id)
        assert result is False

    def test_create_pending_consent(self, repository, user):
        """create_pending_consent creates pending consent record."""
        expires_at = datetime.utcnow() + __import__("datetime").timedelta(hours=48)

        consent = repository.create_pending_consent(
            user_id=user.id,
            student_id=None,
            consent_type="coppa_verifiable",
            token="test-token-123",
            expires_at=expires_at,
        )

        assert consent.user_id == user.id
        assert consent.consent_type == "coppa_verifiable"
        assert consent.status == "pending"
        assert consent.metadata_json is not None
        assert consent.metadata_json.get("token") == "test-token-123"

    def test_confirm_consent(self, repository, user):
        """confirm_consent changes pending to granted."""
        from src.models.models import ConsentRecord, ConsentStatus

        pending = ConsentRecord(
            id="consent-pending",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.PENDING,
            metadata_json={"token": "test-token"},
        )
        repository.session.add(pending)
        repository.session.commit()

        confirmed_at = datetime.utcnow()
        result = repository.confirm_consent("consent-pending", confirmed_at)

        assert result is not None
        assert result.id == "consent-pending"
        assert result.status == ConsentStatus.GRANTED
        assert result.consented_at == confirmed_at
        assert result.metadata_json is not None
        assert "expires_at" in result.metadata_json

    def test_confirm_consent_not_pending(self, repository, user):
        """confirm_consent raises error for non-pending consent."""
        from src.models.models import ConsentRecord, ConsentStatus

        granted = ConsentRecord(
            id="consent-granted",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.GRANTED,
        )
        repository.session.add(granted)
        repository.session.commit()

        with pytest.raises(ValueError, match="Only pending consents"):
            repository.confirm_consent("consent-granted", datetime.utcnow())

    def test_confirm_consent_not_found(self, repository, user):
        """confirm_consent returns None for missing consent."""
        result = repository.confirm_consent("missing-consent", datetime.utcnow())
        assert result is None

    def test_get_consent_status(self, repository, user):
        """get_consent_status returns all consent records for user."""
        from src.models.models import ConsentRecord, ConsentStatus

        consent1 = ConsentRecord(
            id="consent-1",
            user_id=user.id,
            consent_type="data_processing",
            status=ConsentStatus.GRANTED,
        )
        consent2 = ConsentRecord(
            id="consent-2",
            user_id=user.id,
            consent_type="media_sharing",
            status=ConsentStatus.PENDING,
        )
        repository.session.add(consent1)
        repository.session.add(consent2)
        repository.session.commit()

        results = repository.get_consent_status(user.id)

        assert len(results) == 2
        record_ids = {r.id for r in results}
        assert "consent-1" in record_ids
        assert "consent-2" in record_ids

    def test_revoke_consent(self, repository, user):
        """revoke_consent changes status to revoked."""
        from src.models.models import ConsentRecord, ConsentStatus

        consent = ConsentRecord(
            id="consent-1",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.GRANTED,
        )
        repository.session.add(consent)
        repository.session.commit()

        result = repository.revoke_consent("consent-1")

        assert result is not None
        assert result.id == "consent-1"
        assert result.status == ConsentStatus.REVOKED

    def test_revoke_consent_not_found(self, repository, user):
        """revoke_consent returns None for missing consent."""
        result = repository.revoke_consent("missing-consent")
        assert result is None

    def test_get_pending_by_token(self, repository, user):
        """get_pending_by_token retrieves pending consent by token."""
        from src.models.models import ConsentRecord, ConsentStatus

        pending = ConsentRecord(
            id="consent-pending",
            user_id=user.id,
            consent_type="coppa_verifiable",
            status=ConsentStatus.PENDING,
            metadata_json={"token": "test-token-123"},
        )
        repository.session.add(pending)
        repository.session.commit()

        result = repository.get_pending_by_token("test-token-123")

        assert result is not None
        assert result.id == "consent-pending"

    def test_get_pending_by_token_not_found(self, repository, user):
        """get_pending_by_token returns None for missing token."""
        result = repository.get_pending_by_token("missing-token")
        assert result is None
