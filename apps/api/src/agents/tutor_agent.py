"""Tutor Agent — Socratic hints + scaffolded explanations.

PRD Stage 3 § 3.2 Tutor Agent. Routes through `LLMClient(purpose=STUDENT_TUTORING)`
which defaults to Ollama (COPPA non-negotiable). Phase 3 ships a stub that
selects from question-attached hints; Phase 4-B will swap to live LLM
generation with Flesch-Kincaid + banned-phrase validation.
"""

from __future__ import annotations

from typing import Optional

from src.agents.state import SessionState
from src.clients.llm_client import LLMClient, LLMPurpose, get_llm_client


BANNED_PHRASES = [
    "that's wrong",
    "incorrect",
    "you failed",
    "that is not right",
    "wrong answer",
    "you got it wrong",
    "mistaken",
]


def validate_tutor_response(response: str, max_grade: float = 5.5) -> tuple[bool, str]:
    """Phase-3 placeholder: check banned phrases + length.

    Phase 4-B will add Flesch-Kincaid grade-level check via `textstat`.
    """
    if len(response.split()) > 75:
        return False, "too_long"
    lower = response.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lower:
            return False, f"banned_phrase:{phrase}"
    return True, ""


class TutorAgent:
    """Deliver a hint or worked example for the current question."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client or get_llm_client()

    async def deliver_hint(
        self,
        state: SessionState,
        hint_level: int,
    ) -> str:
        """Return a sanitized hint string for `state['current_question']`."""
        question = state.get("current_question") or {}
        # Stub: deterministic, always-safe placeholder. Phase 4-B replaces.
        if hint_level <= 1:
            text = "Let's look at the numbers again. What is the question asking?"
        elif hint_level == 2:
            text = (
                "Try breaking the problem into smaller steps. "
                "What operation matches the words?"
            )
        else:
            text = (
                "Here's a similar example with different numbers. "
                "Try the same approach on yours."
            )
        ok, _ = validate_tutor_response(text)
        # If our own stub ever fails validation it's a code bug; surface it.
        assert ok, "stub hint failed validation"
        return text

    async def __call__(self, state: SessionState) -> SessionState:
        attempts = state.get("attempt_count", 0) + 1
        hint = await self.deliver_hint(state, hint_level=attempts)
        state["last_hint"] = hint  # type: ignore[typeddict-unknown-key]
        state["next_agent"] = "await_answer"
        return state


TUTOR_LLM_PURPOSE = LLMPurpose.STUDENT_TUTORING
