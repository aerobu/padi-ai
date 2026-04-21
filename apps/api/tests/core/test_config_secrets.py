"""Tests for Settings secret requirements — Task 1.7."""
import os
import pytest
from pydantic import ValidationError

# Minimal required env vars for Settings() to succeed (beyond the ones under test)
_REQUIRED_EXTRAS = {
    "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
    "AUTH0_SECRET": "test-secret-value",
    "AUTH0_BASE_URL": "http://localhost:3000",
    "AUTH0_ISSUER_BASE_URL": "https://test.auth0.com",
    "AUTH0_CLIENT_ID": "test-client-id",
    "AUTH0_CLIENT_SECRET": "test-client-secret",
}


def _set_required_extras(monkeypatch):
    """Set all required env vars except the one under test."""
    for key, val in _REQUIRED_EXTRAS.items():
        monkeypatch.setenv(key, val)


def _clear_settings_cache():
    """Clear @lru_cache on get_settings so new env reads take effect."""
    from src.core.config import get_settings
    get_settings.cache_clear()


def test_config_rejects_missing_encryption_passphrase(monkeypatch):
    """Settings must raise when ENCRYPTION_KEY_PASSPHRASE is not set."""
    _set_required_extras(monkeypatch)
    monkeypatch.delenv("ENCRYPTION_KEY_PASSPHRASE", raising=False)
    _clear_settings_cache()
    from src.core.config import Settings
    with pytest.raises(ValidationError):
        Settings(_env_file=os.devnull)


def test_config_rejects_short_encryption_passphrase(monkeypatch):
    """Settings must raise when ENCRYPTION_KEY_PASSPHRASE is shorter than 32 chars."""
    _set_required_extras(monkeypatch)
    monkeypatch.setenv("ENCRYPTION_KEY_PASSPHRASE", "too-short")
    _clear_settings_cache()
    from src.core.config import Settings
    with pytest.raises(ValidationError):
        Settings(_env_file=os.devnull)


def test_config_accepts_strong_encryption_passphrase(monkeypatch):
    """Settings construction succeeds with a 32+ char passphrase."""
    _set_required_extras(monkeypatch)
    monkeypatch.setenv(
        "ENCRYPTION_KEY_PASSPHRASE",
        "x" * 32,
    )
    _clear_settings_cache()
    from src.core.config import Settings
    s = Settings(_env_file=os.devnull)
    assert len(s.ENCRYPTION_KEY_PASSPHRASE) >= 32
