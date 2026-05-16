"""Smoke tests for the practice-session WebSocket endpoint.

Exercises the orchestrator end-to-end over a real WS connection (Starlette
TestClient) with the in-memory Redis fixture. The JWT verification is
bypassed by overriding `_verify_token` so we don't need to mint real Auth0
tokens in the test.
"""

from __future__ import annotations

import json

import pytest
from starlette.testclient import TestClient

from src.api.v1.endpoints import practice_ws
from src.main import app


@pytest.fixture
def ws_client(mock_redis_client):
    """TestClient wired with a stubbed token verifier."""

    async def _ok_verify(_token):
        return {"sub": "stu_test_1"}

    original = practice_ws._verify_token
    practice_ws._verify_token = _ok_verify  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            yield client
    finally:
        practice_ws._verify_token = original  # type: ignore[assignment]


@pytest.mark.integration
def test_ws_starts_session_and_emits_initial_question(ws_client: TestClient):
    """Phase-3 happy path: connect, get a question, ping, end."""
    url = "/api/v1/sessions/sess_smoke_1/ws?token=stub&skill_id=4.NF.A.1"
    with ws_client.websocket_connect(url) as ws:
        msg = ws.receive_text()
        frame = json.loads(msg)
        assert frame["type"] == "question"
        assert frame["session_id"] == "sess_smoke_1"
        assert frame["stem"]
        assert frame["question_id"]

        # Heartbeat
        ws.send_text(json.dumps({"type": "ping"}))
        pong = json.loads(ws.receive_text())
        assert pong == {"type": "pong"}

        # Graceful close
        ws.send_text(json.dumps({"type": "end"}))
        complete = json.loads(ws.receive_text())
        assert complete["type"] == "session_complete"


@pytest.mark.integration
def test_ws_correct_answer_yields_next_question(ws_client: TestClient):
    url = "/api/v1/sessions/sess_smoke_2/ws?token=stub&skill_id=4.NF.A.1"
    with ws_client.websocket_connect(url) as ws:
        first = json.loads(ws.receive_text())
        assert first["type"] == "question"
        # Stub correct answer is always "A"
        ws.send_text(json.dumps({"type": "answer", "answer": "A"}))
        nxt = json.loads(ws.receive_text())
        assert nxt["type"] == "question"
        assert nxt["question_id"] != first["question_id"]
        assert nxt["questions_answered"] == 1


@pytest.mark.integration
def test_ws_wrong_answer_yields_hint_not_progress(ws_client: TestClient):
    url = "/api/v1/sessions/sess_smoke_3/ws?token=stub&skill_id=4.NF.A.1"
    with ws_client.websocket_connect(url) as ws:
        ws.receive_text()  # initial question
        ws.send_text(json.dumps({"type": "answer", "answer": "Z"}))
        frame = json.loads(ws.receive_text())
        assert frame["type"] == "hint"
        assert frame["hint"]
        assert frame["hint_level"] == 1


@pytest.mark.integration
def test_ws_rejects_missing_token(ws_client: TestClient):
    """Without a token query param the server should refuse the upgrade."""
    # Override the stub back to the real verifier for this one test
    async def _none(_t):
        return None

    practice_ws._verify_token = _none  # type: ignore[assignment]
    try:
        url = "/api/v1/sessions/sess_no_auth/ws?skill_id=4.NF.A.1"
        with pytest.raises(Exception):
            with ws_client.websocket_connect(url):
                pass
    finally:
        # The fixture finalizer will reset, but be tidy.
        pass
