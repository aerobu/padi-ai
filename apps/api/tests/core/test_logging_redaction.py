"""Verify PIIRedactionFilter strips emails / phones / sensitive keys."""

from __future__ import annotations

import logging

import pytest

from src.core.logging import (
    PIIRedactionFilter,
    SENSITIVE_KEYS,
    _redact_obj,
    _redact_str,
)


@pytest.mark.unit
def test_email_is_redacted_from_string():
    assert "parent@example.com" not in _redact_str("user parent@example.com logged in")


@pytest.mark.unit
def test_phone_is_redacted_from_string():
    assert "5551234567" not in _redact_str("call 5551234567 now")


@pytest.mark.unit
def test_sensitive_keys_redacted_in_dict():
    payload = {"email": "x@y.com", "id": "stu_1", "password": "hunter2"}
    out = _redact_obj(payload)
    assert out["email"] == "<redacted>"
    assert out["password"] == "<redacted>"
    assert out["id"] == "stu_1"


@pytest.mark.unit
def test_filter_strips_pii_from_log_records(caplog: pytest.LogCaptureFixture):
    logger = logging.getLogger("padi.test")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    flt = PIIRedactionFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(flt)
    try:
        with caplog.at_level(logging.INFO):
            caplog.handler.addFilter(flt)
            logger.info("registering user alice@padi.ai for grade 4")
        assert "alice@padi.ai" not in caplog.text
        assert "<redacted>" in caplog.text
    finally:
        for handler in logging.getLogger().handlers:
            handler.removeFilter(flt)


@pytest.mark.unit
def test_sensitive_keys_set_is_canonical():
    # If someone adds a sensitive key it should be lowercase to match filter.
    assert all(k == k.lower() for k in SENSITIVE_KEYS)
