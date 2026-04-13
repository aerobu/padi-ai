"""Tests for core configuration."""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestSettings:
    """Test settings loading and validation."""

    def test_settings_load_from_env(self):
        """Settings loads environment variables correctly."""
        from src.core.config import get_settings

        settings = get_settings()

        assert settings is not None
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'AUTH0_SECRET')

    def test_default_values(self):
        """Default values are set correctly."""
        from src.core.config import get_settings

        settings = get_settings()

        # Check environment defaults
        assert settings.ENVIRONMENT in ["development", "staging", "production"]


class TestEnvironmentConfig:
    """Test environment-specific configuration."""

    def test_development_defaults(self):
        """Development environment has appropriate defaults."""
        from src.core.config import get_settings

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            # Clear the cached settings
            import src.core.config
            src.core.config._settings = None

            settings = get_settings()

            assert settings.ENVIRONMENT == "development"


class TestLLMRoutingConfig:
    """Test LLM routing configuration."""

    def test_llm_routing_configured(self):
        """LLM routing models are configured."""
        from src.core.config import get_settings

        settings = get_settings()

        assert hasattr(settings, 'LLM_ROUTING__TUTOR')
        assert hasattr(settings, 'LLM_ROUTING__ASSESSMENT')

    def test_ollama_url_configurable(self):
        """Ollama base URL is configurable."""
        from src.core.config import get_settings

        settings = get_settings()

        assert hasattr(settings, 'OLLAMA_BASE_URL')

    def test_llm_timeout_configured(self):
        """LLM timeout is configured."""
        from src.core.config import get_settings

        settings = get_settings()

        assert hasattr(settings, 'LLM_TIMEOUT_SECONDS')
        assert settings.LLM_TIMEOUT_SECONDS > 0
