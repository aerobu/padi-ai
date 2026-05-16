"""Structured-logging utilities with COPPA-aware PII redaction.

Two pieces:
1. `PIIRedactionFilter` — strips email addresses, common phone-number patterns,
   and likely-PII keys from log records and their `extra` payload.
2. `configure_logging()` — sets up the root logger to use a JSON formatter
   (when LOG_FORMAT="json") with the redaction filter attached to every
   handler. Idempotent.

These exist because raw `logger.info(f"... {email} ...")` patterns leak PII
into logs, which is a COPPA non-starter. Going forward, prefer
`logger.info("event", extra={"event": "X", "ids": {…}})`.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
# Conservative phone matcher (NA + EU + bare 10+ digit runs)
PHONE_RE = re.compile(r"\b(?:\+?\d[\s\-.]?){7,15}\d\b")

# Keys whose values should be wholly redacted when seen in `extra`/`payload`
SENSITIVE_KEYS = {
    "email",
    "password",
    "secret",
    "token",
    "access_token",
    "id_token",
    "refresh_token",
    "authorization",
    "first_name",
    "last_name",
    "display_name",
    "student_answer",
    "answer_text",
    "question_text",
    "stem",
    "phone",
    "address",
}

_REDACTED = "<redacted>"


def _redact_str(value: str) -> str:
    """Mask emails and phone numbers in any free-text string."""
    value = EMAIL_RE.sub(_REDACTED, value)
    value = PHONE_RE.sub(_REDACTED, value)
    return value


def _redact_obj(obj: Any) -> Any:
    """Recursively redact PII inside dicts/lists/tuples (best-effort)."""
    if isinstance(obj, dict):
        return {
            k: (_REDACTED if k.lower() in SENSITIVE_KEYS else _redact_obj(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_obj(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_redact_obj(v) for v in obj)
    if isinstance(obj, str):
        return _redact_str(obj)
    return obj


class PIIRedactionFilter(logging.Filter):
    """Strip PII from `LogRecord.msg`, `args`, and any extra payload."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        if isinstance(record.msg, str):
            record.msg = _redact_str(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = _redact_obj(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(_redact_obj(a) for a in record.args)
        # Sanitize any structured fields callers attach via `extra=`.
        for attr in list(record.__dict__):
            if attr in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process",
                "taskName",
            }:
                continue
            value = getattr(record, attr)
            if attr.lower() in SENSITIVE_KEYS:
                setattr(record, attr, _REDACTED)
            else:
                setattr(record, attr, _redact_obj(value))
        return True


class JSONFormatter(logging.Formatter):
    """Minimal JSON log formatter — no external dep."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Surface attached extras that aren't standard LogRecord fields.
        std = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "taskName",
        }
        for attr, val in record.__dict__.items():
            if attr in std or attr in payload:
                continue
            try:
                json.dumps(val)  # ensure serializable
            except (TypeError, ValueError):
                val = repr(val)
            payload[attr] = val
        return json.dumps(payload, ensure_ascii=False, default=str)


_CONFIGURED = False


def configure_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Configure the root logger once, with redaction on every handler."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(level)
    # Remove any handlers attached by other libraries so our config wins.
    root.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(
        JSONFormatter()
        if fmt == "json"
        else logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    handler.addFilter(PIIRedactionFilter())
    root.addHandler(handler)
    _CONFIGURED = True
