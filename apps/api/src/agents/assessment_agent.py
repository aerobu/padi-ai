"""Assessment Agent — evaluate student answers and classify error types.

Stage 3 PRD § 3.2 Assessment Agent. The agent runs through `LLMClient` with
`purpose=ASSESSMENT` so model selection (Ollama default; cloud only with a
COPPA DPA in place) stays centralized.

This module ships with a deterministic no-op evaluator so the orchestrator
can be wired and tested end-to-end before the prompt engineering is finalized
in Phase 4-A.
"""

from __future__ import annotations

from typing import Optional, TypedDict

from src.agents.state import SessionState
from src.clients.llm_client import LLMClient, LLMPurpose, get_llm_client


class AssessmentResult(TypedDict, total=False):
    is_correct: bool
    normalized_answer: str
    error_type: Optional[str]
    error_code: Optional[str]
    feedback_level: int
    partial_credit: bool
    confidence: float
    assessment_reasoning: str


def _string_equivalence(student_answer: str, correct_answer: str) -> bool:
    """Loose equality used as the Phase-3 stub. Phase 4-A will swap to an
    LLM-backed evaluator with the Stage-3 error taxonomy."""
    return student_answer.strip().lower() == correct_answer.strip().lower()


class AssessmentAgent:
    """Evaluates the current question's response in `SessionState`."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client or get_llm_client()

    async def evaluate(
        self,
        state: SessionState,
        student_answer: str,
    ) -> AssessmentResult:
        question = state.get("current_question") or {}
        correct = str(question.get("correct_answer", ""))
        is_correct = _string_equivalence(student_answer, correct)
        return AssessmentResult(
            is_correct=is_correct,
            normalized_answer=student_answer.strip(),
            error_type=None if is_correct else "unclassified",
            error_code=None if is_correct else "ERR-UNCLASSIFIED",
            feedback_level=0 if is_correct else min(state.get("attempt_count", 0) + 1, 3),
            partial_credit=False,
            confidence=1.0 if is_correct else 0.6,
            assessment_reasoning=(
                "exact_match" if is_correct else "stub_classifier"
            ),
        )

    async def __call__(self, state: SessionState) -> SessionState:
        """LangGraph node entry. Reads `state['last_student_answer']` and
        updates `state['last_assessment']`."""
        answer = str(state.get("last_student_answer", ""))  # type: ignore[typeddict-item]
        result = await self.evaluate(state, answer)
        # Augment state in place — orchestrator owns the dict mutation pattern.
        state["last_assessment"] = result  # type: ignore[typeddict-unknown-key]
        state["next_agent"] = "progress_tracker"
        return state


# Purpose marker so callers know this agent is COPPA-routed to Ollama.
ASSESSMENT_LLM_PURPOSE = LLMPurpose.ASSESSMENT
