"""Tests for standards API endpoints."""

import pytest
from unittest.mock import patch, MagicMock


class TestListStandardsEndpoint:
    """Test GET /standards endpoint."""

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
                "sub": "parent-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock standard service."""
        with patch("src.api.v1.endpoints.standards.get_standard_service") as mock:
            mock_service = MagicMock()
            mock_service.list_standards = MagicMock()
            mock_service.list_standards.return_value = [
                {
                    "standard_id": "std-1",
                    "standard_code": "4.NBT.A.1",
                    "domain": "Numbers and Operations",
                    "grade_level": 4,
                },
                {
                    "standard_id": "std-2",
                    "standard_code": "4.NF.A.1",
                    "domain": "Fractions",
                    "grade_level": 4,
                },
            ]
            mock.return_value = mock_service
            yield mock_service

    def test_list_standards_success(self, client, mock_jwt, mock_service):
        """list_standards returns 200 with standards."""
        response = client.get("/api/v1/standards")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["standard_code"] == "4.NBT.A.1"
        mock_service.list_standards.assert_called_once()

    def test_list_standards_with_grade_filter(self, client, mock_jwt, mock_service):
        """list_standards filters by grade."""
        response = client.get("/api/v1/standards?grade=4")

        assert response.status_code == 200
        mock_service.list_standards.assert_called_once_with(grade=4)

    def test_list_standards_with_domain_filter(self, client, mock_jwt, mock_service):
        """list_standards filters by domain."""
        response = client.get("/api/v1/standards?domain=Numbers%20and%20Operations")

        assert response.status_code == 200
        mock_service.list_standards.assert_called_once()


class TestGetStandardEndpoint:
    """Test GET /standards/{code} endpoint."""

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
                "sub": "parent-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock standard service."""
        with patch("src.api.v1.endpoints.standards.get_standard_service") as mock:
            mock_service = MagicMock()
            mock_service.get_standard = MagicMock()
            mock_service.get_standard.return_value = {
                "standard_id": "std-1",
                "standard_code": "4.NBT.A.1",
                "domain": "Numbers and Operations",
                "title": "Place Value",
                "description": "Understand place value relationships",
                "grade_level": 4,
            }
            mock.return_value = mock_service
            yield mock_service

    def test_get_standard_success(self, client, mock_jwt, mock_service):
        """get_standard returns 200 with standard data."""
        response = client.get("/api/v1/standards/4.NBT.A.1")

        assert response.status_code == 200
        data = response.json()
        assert data["standard_code"] == "4.NBT.A.1"
        assert data["title"] == "Place Value"
        mock_service.get_standard.assert_called_once_with("4.NBT.A.1")

    def test_get_standard_not_found(self, client, mock_jwt, mock_service):
        """get_standard returns 404 for missing standard."""
        mock_service.get_standard.side_effect = ValueError("Standard not found")

        response = client.get("/api/v1/standards/4.NonExistent.A.1")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
