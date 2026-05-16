"""WebSocket endpoint for live adaptive-practice sessions.

PRD Stage 3 § 3.2: the orchestrator runs over a long-lived WebSocket so
the tutor and assessment agents can interleave naturally with student
answer events. This Phase-3 implementation:

1. Accepts `WS /api/v1/sessions/{session_id}/ws?token=<jwt>` (token in the
   query string — many browser WebSocket clients can't set headers).
2. Verifies the JWT on connect.
3. Loads SessionState from Redis (cold start: starts a new session).
4. Drives `SessionOrchestrator.submit_answer` per inbound message.
5. Emits `question` / `hint` / `session_complete` frames.

The agent stubs in `src/agents/` return deterministic placeholders so the
endpoint can be smoke-tested end-to-end before Phase 4 fills in the real
LLM-backed implementations.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jwt.exceptions import InvalidTokenError

from src.agents.orchestrator import SessionOrchestrator
from src.agents.state import SessionState
from src.core.config import get_settings
from src.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Reuse the assessment-state Redis namespace for session-state storage,
# but with a different key prefix so collisions are impossible.
_SESSION_STATE_PREFIX = "ws_session"


def _state_key(session_id: str) -> str:
    return f"{_SESSION_STATE_PREFIX}:{session_id}:state"


async def _verify_token(token: str | None) -> dict[str, Any] | None:
    """Decode and validate the JWT passed via query string."""
    if not token:
        return None
    try:
        from src.core.security import get_jwks_client

        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE or settings.AUTH0_CLIENT_ID,
            issuer=settings.AUTH0_ISSUER_BASE_URL,
        )
    except (InvalidTokenError, Exception):
        logger.warning("WS token verification failed")
        return None


def _serialize_state(state: SessionState) -> str:
    """JSON-encode SessionState (datetimes → isoformat)."""

    def default(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Cannot serialize {type(obj).__name__}")

    return json.dumps(dict(state), default=default)


def _deserialize_state(payload: str) -> SessionState:
    return json.loads(payload)


def _question_frame(state: SessionState) -> dict[str, Any]:
    q = state.get("current_question") or {}
    return {
        "type": "question",
        "session_id": state.get("session_id"),
        "question_id": q.get("question_id"),
        "stem": q.get("question_text"),
        "question_type": q.get("question_type"),
        "options": q.get("options"),
        "attempt_count": state.get("attempt_count", 0),
        "questions_answered": state.get("questions_answered", 0),
    }


def _hint_frame(state: SessionState) -> dict[str, Any]:
    return {
        "type": "hint",
        "session_id": state.get("session_id"),
        "hint": state.get("last_hint"),
        "hint_level": state.get("attempt_count", 0),
    }


def _complete_frame(state: SessionState) -> dict[str, Any]:
    return {
        "type": "session_complete",
        "session_id": state.get("session_id"),
        "questions_answered": state.get("questions_answered", 0),
        "questions_correct": state.get("questions_correct", 0),
        "bkt_states": state.get("bkt_states", {}),
    }


@router.websocket("/sessions/{session_id}/ws")
async def practice_session_ws(
    websocket: WebSocket,
    session_id: str,
    token: str | None = None,
    student_id: str | None = None,
    skill_id: str | None = None,
    learning_plan_id: str | None = None,
) -> None:
    """Long-lived WebSocket for an adaptive practice session.

    Inbound messages (JSON):
        {"type": "answer", "answer": "B"}      — student response
        {"type": "ping"}                       — heartbeat
        {"type": "end"}                        — graceful close

    Outbound messages (JSON):
        {"type": "question", ...}              — new question to render
        {"type": "hint", ...}                  — tutor hint after wrong answer
        {"type": "session_complete", ...}      — session ended
        {"type": "error", "message": "..."}    — recoverable error
    """
    payload = await _verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="unauthorized")
        return

    await websocket.accept()
    sub = payload.get("sub") or payload.get("auth0_id") or ""
    effective_student = student_id or sub

    redis = get_redis_client()
    orch = SessionOrchestrator()

    # Cold-start: if no session state in Redis, kick off a new one.
    raw = await redis.get(_state_key(session_id))
    if raw is None:
        if not skill_id:
            await websocket.send_text(
                json.dumps({"type": "error", "message": "missing skill_id for new session"})
            )
            await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
            return
        state = await orch.start_session(
            student_id=effective_student,
            session_id=session_id,
            learning_plan_id=learning_plan_id or "",
            current_skill_id=skill_id,
        )
    else:
        state = _deserialize_state(raw if isinstance(raw, str) else raw.decode("utf-8"))

    # Send the initial question
    await websocket.send_text(json.dumps(_question_frame(state)))
    await redis.set(_state_key(session_id), _serialize_state(state), ex=1800)

    try:
        while True:
            raw_in = await websocket.receive_text()
            try:
                msg = json.loads(raw_in)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "bad_json"}))
                continue

            mtype = msg.get("type")
            if mtype == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            if mtype == "end":
                state["session_complete"] = True
                await websocket.send_text(json.dumps(_complete_frame(state)))
                break
            if mtype != "answer":
                await websocket.send_text(json.dumps({"type": "error", "message": f"unknown_type:{mtype}"}))
                continue

            answer = str(msg.get("answer", ""))
            state = await orch.submit_answer(state, answer)
            await redis.set(_state_key(session_id), _serialize_state(state), ex=1800)

            if state.get("session_complete"):
                await websocket.send_text(json.dumps(_complete_frame(state)))
                break
            if state.get("last_hint") and state.get("next_agent") == "await_answer":
                await websocket.send_text(json.dumps(_hint_frame(state)))
                # Don't clear last_hint until the next question is emitted —
                # so the client always knows the latest hint shown.
                continue
            # Otherwise the orchestrator advanced to a new question
            await websocket.send_text(json.dumps(_question_frame(state)))

    except WebSocketDisconnect:
        logger.info("WS disconnected: session_id=%s", session_id)
        # State already persisted on each turn; nothing to do.
