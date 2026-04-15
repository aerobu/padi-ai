"""Tests for consent API endpoints."""

import pytest
from unittest.mock import patch, MagicMock


class TestConsentInitiateEndpoint:
    """Test POST /consent/initiate endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "user-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock consent service."""
        with patch("src.api.v1.endpoints.consent.get_consent_service") as mock:
            mock_service = MagicMock()
            mock_service.initiate_consent = MagicMock()
            mock_service.initiate_consent.return_value = {
                "consent_id": "consent-123",
                "status": "pending",
                "email_sent_to": "p***@example.com",
                "expires_at": "2026-04-15T12:00:00",
                "verification_token": "token-abc",
            }
            mock.return_value = mock_service
            yield mock_service

    def test_initiate_consent_success(self, client, mock_jwt, mock_service):
        """initiate_consent returns 201 on success."""
        response = client.post(
            "/api/v1/consent/initiate",
            json={
                "student_display_name": "Test Student",
                "grade_level": 4,
                "acknowledgements": [
                    "data_collection",
                    "data_use",
                    "third_party_disclosure",
                    "parental_rights",
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["consent_id"] == "consent-123"
        assert data["status"] == "pending"
        mock_service.initiate_consent.assert_called_once()

    def test_initiate_consent_missing_acknowledgements(self, client, mock_jwt, mock_service):
        """initiate_consent returns 400 for missing acknowledgements."""
        mock_service.initiate_consent.side_effect = ValueError(
            "All required consent clauses must be acknowledged"
        )

        response = client.post(
            "/api/v1/consent/initiate",
            json={
                "student_display_name": "Test Student",
                "acknowledgements": ["data_collection"],  # Missing others
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_initiate_consent_existing_consent(self, client, mock_jwt, mock_service):
        """initiate_consent returns 400 for existing consent."""
        mock_service.initiate_consent.side_effect = ValueError(
            "Active consent already exists"
        )

        response = client.post(
            "/api/v1/consent/initiate",
            json={
                "student_display_name": "Test Student",
                "acknowledgements": [
                    "data_collection",
                    "data_use",
                    "third_party_disclosure",
                    "parental_rights",
                ],
            },
        )

        assert response.status_code == 400


class TestConsentConfirmEndpoint:
    """Test POST /consent/confirm endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "user-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock consent service."""
        with patch("src.api.v1.endpoints.consent.get_consent_service") as mock:
            mock_service = MagicMock()
            mock_service.confirm_consent = MagicMock()
            mock_service.confirm_consent.return_value = {
                "consent_id": "consent-123",
                "status": "active",
                "confirmed_at": "2026-04-14T12:00:00",
                "expires_at": "2027-04-14T12:00:00",
            }
            mock.return_value = mock_service
            yield mock_service

    def test_confirm_consent_success(self, client, mock_jwt, mock_service):
        """confirm_consent returns 200 on success."""
        response = client.post(
            "/api/v1/consent/confirm",
            json={"token": "valid-token-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["consent_id"] == "consent-123"
        mock_service.confirm_consent.assert_called_once_with("valid-token-123")

    def test_confirm_consent_invalid_token(self, client, mock_jwt, mock_service):
        """confirm_consent returns 400 for invalid token."""
        mock_service.confirm_consent.side_effect = ValueError(
            "Invalid or expired consent token"
        )

        response = client.post(
            "/api/v1/consent/confirm",
            json={"token": "invalid-token"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_confirm_consent_expired_token(self, client, mock_jwt, mock_service):
        """confirm_consent returns 400 for expired token."""
        mock_service.confirm_consent.side_effect = ValueError(
            "Consent token has expired"
        )

        response = client.post(
            "/api/v1/consent/confirm",
            json={"token": "expired-token"},
        )

        assert response.status_code == 400


class TestConsentStatusEndpoint:
    """Test GET /consent/status endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "user-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock consent service."""
        with patch("src.api.v1.endpoints.consent.get_consent_service") as mock:
            mock_service = MagicMock()
            mock_service.get_consent_status = MagicMock()
            mock_service.get_consent_status.return_value = {
                "has_active_consent": True,
                "consent_records": [
                    {
                        "consent_id": "consent-123",
                        "consent_type": "coppa_verifiable",
                        "status": "granted",
                    }
                ],
            }
            mock.return_value = mock_service
            yield mock_service

    def test_get_consent_status_success(self, client, mock_jwt, mock_service):
        """get_consent_status returns 200 with status."""
        response = client.get("/api/v1/consent/status")

        assert response.status_code == 200
        data = response.json()
        assert data["has_active_consent"] is True
        assert len(data["consent_records"]) == 1
        mock_service.get_consent_status.assert_called_once_with("user-123")
