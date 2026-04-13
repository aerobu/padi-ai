"""Tests for health check endpoints."""

import pytest
from starlette.testclient import TestClient


class TestHealthEndpoints:
    """Test health check API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for API tests."""
        from src.main import app
        return TestClient(app)

    def test_root_health_endpoint(self, client):
        """Root /health endpoint returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_api_health_endpoint(self, client):
        """API health endpoint returns detailed status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Should have basic status
        assert "status" in data
        # Status can be 'ok' or 'healthy' depending on implementation
        assert data["status"] in ["ok", "healthy"]

        # Should have version info
        assert "version" in data

    def test_api_health_llm_endpoint(self, client):
        """LLM health endpoint returns model status."""
        response = client.get("/api/v1/health/llm")

        assert response.status_code == 200
        data = response.json()

        # Should have status and model info
        assert "status" in data
        assert "tutor_model" in data
        assert "ollama_status" in data

    def test_api_health_ready_endpoint(self, client):
        """Ready endpoint checks database connectivity."""
        response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()

        # Should indicate readiness
        assert "status" in data
        assert data["status"] in ["ready", "not_ready"]

    def test_api_health_live_endpoint(self, client):
        """Live endpoint checks process liveness."""
        response = client.get("/api/v1/health/live")

        assert response.status_code == 200
        data = response.json()

        # Should always be alive
        assert data["status"] == "alive"


class TestHealthEndpointPerformance:
    """Test health endpoint performance."""

    @pytest.fixture
    def client(self):
        """Create test client for API tests."""
        from src.main import app
        return TestClient(app)

    def test_health_response_time(self, client):
        """Health endpoint responds within 200ms."""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"Health endpoint took {elapsed:.2f}ms"

    def test_health_endpoint_consistency(self, client):
        """Health endpoint returns consistent format."""
        import json

        responses = []
        for _ in range(5):
            response = client.get("/api/v1/health")
            responses.append(json.loads(response.text))

        # All responses should have same keys
        keys = [set(r.keys()) for r in responses]
        assert all(k == keys[0] for k in keys)
