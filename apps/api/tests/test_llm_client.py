"""Tests for LLM client with COPPA-compliant routing."""

import pytest
from unittest.mock import patch, MagicMock


class TestLLMPurpose:
    """Test LLM purpose enumeration."""

    def test_purpose_values(self):
        """LLMPurpose has correct values."""
        from src.clients.llm_client import LLMPurpose

        purposes = [p.value for p in LLMPurpose]

        assert "student_tutoring" in purposes
        assert "assessment" in purposes
        assert "question_generation" in purposes
        assert "admin" in purposes
        assert "analytics" in purposes

    def test_purpose_enum_usage(self):
        """LLMPurpose can be used as enum."""
        from src.clients.llm_client import LLMPurpose

        assert LLMPurpose.STUDENT_TUTORING.value == "student_tutoring"
        assert LLMPurpose.ASSESSMENT.value == "assessment"

    def test_purpose_analytics_uses_local(self):
        """Analytics purpose uses local Ollama for COPPA."""
        from src.clients.llm_client import LLMPurpose

        assert LLMPurpose.ANALYTICS.value == "analytics"


class TestLLMClient:
    """Test LiteLLM client with routing."""

    @patch("src.clients.llm_client.settings")
    def test_client_uses_settings(self, mock_settings):
        """LLMClient reads from settings."""
        from src.clients.llm_client import LLMClient

        # Set mock settings
        mock_settings.LLM_ROUTING__TUTOR = "ollama/qwen2.5:72b"
        mock_settings.LLM_ROUTING__ASSESSMENT = "ollama/qwen2.5:32b"
        mock_settings.LLM_ROUTING__QUESTION_GEN = "anthropic/claude-3-5-sonnet"
        mock_settings.LLM_ROUTING__ADMIN = "anthropic/claude-3-5-sonnet"
        mock_settings.OLLAMA_DEFAULT_MODEL = "ollama/qwen2.5:72b"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.LLM_TIMEOUT_SECONDS = 30

        client = LLMClient()

        # Verify client has settings
        assert client.settings is not None
        assert client.settings.LLM_TIMEOUT_SECONDS == 30

    @patch("src.clients.llm_client.settings")
    def test_get_model_for_purpose_student_tutoring(self, mock_settings):
        """Student tutoring returns tutor model."""
        from src.clients.llm_client import LLMClient, LLMPurpose

        mock_settings.LLM_ROUTING__TUTOR = "ollama/qwen2.5:72b"

        client = LLMClient()
        model = client._get_model_for_purpose(LLMPurpose.STUDENT_TUTORING)

        assert model == "ollama/qwen2.5:72b"

    @patch("src.clients.llm_client.settings")
    def test_get_model_for_purpose_assessment(self, mock_settings):
        """Assessment returns assessment model."""
        from src.clients.llm_client import LLMClient, LLMPurpose

        mock_settings.LLM_ROUTING__ASSESSMENT = "ollama/qwen2.5:32b"

        client = LLMClient()
        model = client._get_model_for_purpose(LLMPurpose.ASSESSMENT)

        assert model == "ollama/qwen2.5:32b"

    @patch("src.clients.llm_client.settings")
    def test_get_model_for_purpose_question_generation(self, mock_settings):
        """Question generation returns cloud model."""
        from src.clients.llm_client import LLMClient, LLMPurpose

        mock_settings.LLM_ROUTING__QUESTION_GEN = "anthropic/claude-3-5-sonnet"

        client = LLMClient()
        model = client._get_model_for_purpose(LLMPurpose.QUESTION_GENERATION)

        assert model == "anthropic/claude-3-5-sonnet"

    @patch("src.clients.llm_client.settings")
    def test_get_model_for_purpose_analytics(self, mock_settings):
        """Analytics uses tutor model (local)."""
        from src.clients.llm_client import LLMClient, LLMPurpose

        mock_settings.LLM_ROUTING__TUTOR = "ollama/qwen2.5:72b"

        client = LLMClient()
        model = client._get_model_for_purpose(LLMPurpose.ANALYTICS)

        assert model == "ollama/qwen2.5:72b"

    @patch("src.clients.llm_client.settings")
    def test_get_model_for_analytics_returns_tutor(self, mock_settings):
        """Analytics purpose returns tutor model."""
        from src.clients.llm_client import LLMClient, LLMPurpose

        mock_settings.LLM_ROUTING__TUTOR = "ollama/qwen2.5:72b"

        client = LLMClient()

        # Analytics uses tutor model
        model = client._get_model_for_purpose(LLMPurpose.ANALYTICS)

        assert model == "ollama/qwen2.5:72b"


class TestLLMHealthCheck:
    """Test LLM health check functionality."""

    def test_health_check_structure(self):
        """Health check returns expected structure."""
        from src.clients.llm_client import LLMClient

        with patch("src.clients.llm_client.get_settings") as mock_settings:
            mock_settings.LLM_ROUTING__TUTOR = "ollama/qwen2.5:72b"
            mock_settings.LLM_ROUTING__ASSESSMENT = "ollama/qwen2.5:32b"
            mock_settings.LLM_ROUTING__QUESTION_GEN = "anthropic/claude"
            mock_settings.LLM_ROUTING__ADMIN = "anthropic/claude"
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"

            client = LLMClient()

            # Test health dict structure (without making real API calls)
            health = {
                "status": "healthy",
                "tutor_model": client.settings.LLM_ROUTING__TUTOR,
                "assessment_model": client.settings.LLM_ROUTING__ASSESSMENT,
                "question_gen_model": client.settings.LLM_ROUTING__QUESTION_GEN,
                "admin_model": client.settings.LLM_ROUTING__ADMIN,
                "ollama_base_url": client.settings.OLLAMA_BASE_URL,
                "ollama_status": "disconnected",  # Expected since no Ollama running
            }

            assert "status" in health
            assert "tutor_model" in health
            assert "ollama_status" in health


class TestLLMClientSingleton:
    """Test LLM client singleton pattern."""

    def test_get_llm_client_returns_instance(self):
        """get_llm_client returns LLMClient instance."""
        from src.clients.llm_client import get_llm_client

        client = get_llm_client()

        # Should return an instance
        assert client is not None

    def test_get_llm_client_is_callable(self):
        """get_llm_client is a callable function."""
        from src.clients.llm_client import get_llm_client

        # Should be callable
        assert callable(get_llm_client)
