"""Assessment Agent — evaluate student answers and classify error types.

Stage 3 PRD § 3.2 Assessment Agent. The agent runs through `LLMClient` with
`purpose=ASSESSMENT` so model selection (Ollama default; cloud only with a
COPPA DPA in place) stays centralized.

Phase 4-A wires the real LLM evaluator with a 15-code Grade 4 error taxonomy.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from src.agents.state import AssessmentResult, SessionState
from src.clients.llm_client import LLMClient, LLMPurpose, get_llm_client

logger = logging.getLogger(__name__)


ERROR_TAXONOMY: dict[str, str] = {
    "ERR-PLACE-VALUE": "Misunderstood positional notation (hundreds/tens/ones)",
    "ERR-CARRYING": "Forgot or mis-applied carry/borrow in addition/subtraction",
    "ERR-MULT-FACT": "Recalled a times-table fact incorrectly",
    "ERR-DIV-FACT": "Division fact or long-division step error",
    "ERR-OP-SELECT": "Applied wrong operation (e.g., added instead of multiplied)",
    "ERR-FRACTION-EQ": "Failed to find a common denominator or reduce a fraction",
    "ERR-FRACTION-PART": "Confused numerator/denominator or mixed-number conversion",
    "ERR-UNIT-CONVERT": "Got the magnitude wrong when converting between units",
    "ERR-ROUNDING": "Rounded to wrong place value or used wrong rule",
    "ERR-COMPARISON": "Incorrect inequality (< vs >) or ordering of numbers",
    "ERR-PARTIAL-PROC": "Stopped calculation mid-way (set up correctly but did not finish)",
    "ERR-TRANSCRIPTION": "Copied a digit or symbol from the problem incorrectly",
    "ERR-CONCEPTUAL": "Correct procedure but wrong underlying concept",
    "ERR-COMPUTATION": "General arithmetic slip not covered by above codes",
    "ERR-UNCLASSIFIED": "Cannot determine error type from available information",
}


def _build_system_prompt() -> str:
    """System prompt for the LLM-backed assessment evaluator."""
    taxonomy_list = "\n".join(
        f"- {code}: {desc}" for code, desc in ERROR_TAXONOMY.items()
    )
    return f"""You are an expert Grade 4 mathematics evaluator for PADI.AI, an adaptive tutoring system for Oregon students.

Your task is to evaluate a student's answer against the correct answer and classify any errors using a fixed taxonomy.

ERROR TAXONOMY (use these exact codes):
{taxonomy_list}

You must respond with ONLY a valid JSON object conforming exactly to this schema:
{{
  "is_correct": <boolean — true if the student's answer is mathematically equivalent to the correct answer>,
  "normalized_answer": <string — the student's answer stripped of leading/trailing whitespace>,
  "error_code": <string from the taxonomy above, or null if is_correct is true>,
  "error_type": <human-readable name of the error code, or null if is_correct is true>,
  "partial_credit": <float between 0.0 and 1.0 — 1.0 if correct, 0.5 if setup correct but arithmetic wrong on a multi_step question, 0.0 otherwise>,
  "confidence": <float between 0.0 and 1.0 — your confidence in this classification>,
  "feedback_level": <one of: "correct", "minor_error", "major_error", "conceptual_gap">,
  "assessment_reasoning": <1–2 sentence explanation of your reasoning, for internal audit only — never shown to the student>
}}

Rules:
- For multiple_choice and numeric question types, partial_credit must be 0.0 or 1.0 only (no in-between).
- For multi_step question types, partial_credit may be 0.5 if the student demonstrated correct setup but made an arithmetic error.
- confidence must reflect how certain you are about the error classification, not whether the student is correct.
- feedback_level must be "correct" when is_correct is true.
- error_code and error_type must both be null when is_correct is true.
- Do not include any text outside the JSON object."""


def _build_user_prompt(
    question_text: str,
    correct_answer: str,
    student_answer: str,
    question_type: str,
    attempt_number: int,
) -> str:
    """User prompt for the LLM evaluator."""
    return f"""Question: {question_text}
Correct answer: {correct_answer}
Student's answer: {student_answer}
Question type: {question_type}
Attempt number: {attempt_number}

Evaluate whether the student's answer is correct and classify any error. Return only the JSON object."""


def _clamp_confidence(value: float) -> float:
    """Clamp confidence to [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def _parse_llm_response(content: str) -> AssessmentResult:
    """Parse and validate LLM response JSON.

    Raises: ValueError if JSON is invalid or missing required fields.
    """
    data = json.loads(content)

    is_correct = bool(data.get("is_correct", False))
    normalized_answer = str(data.get("normalized_answer", ""))
    error_code = data.get("error_code")
    error_type = data.get("error_type")
    partial_credit = float(data.get("partial_credit", 0.0))
    confidence = _clamp_confidence(float(data.get("confidence", 0.8)))
    assessment_reasoning = str(data.get("assessment_reasoning", ""))

    feedback_level = data.get("feedback_level", "major_error")
    if feedback_level not in ("correct", "minor_error", "major_error", "conceptual_gap"):
        feedback_level = "major_error"

    return AssessmentResult(
        is_correct=is_correct,
        normalized_answer=normalized_answer,
        error_type=error_type,
        error_code=error_code,
        partial_credit=max(0.0, min(1.0, partial_credit)),
        confidence=confidence,
        feedback_level=feedback_level,  # type: ignore[assignment]
        assessment_reasoning=assessment_reasoning,
    )


def _string_equivalence(student_answer: str, correct_answer: str) -> bool:
    """Fallback equality check when LLM call fails."""
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
        """Evaluate student answer via LLM with taxonomy classification.

        Falls back to string equivalence if LLM call fails.
        """
        question = state.get("current_question") or {}
        correct = str(question.get("correct_answer", ""))
        question_text = str(question.get("question_text", ""))
        question_type = str(question.get("question_type", "multiple_choice"))
        attempt_count = int(state.get("attempt_count", 0))

        messages = [
            {"role": "system", "content": _build_system_prompt()},
            {
                "role": "user",
                "content": _build_user_prompt(
                    question_text=question_text,
                    correct_answer=correct,
                    student_answer=student_answer,
                    question_type=question_type,
                    attempt_number=attempt_count,
                ),
            },
        ]

        try:
            response = await self.llm_client.acomplete(
                messages,
                purpose=LLMPurpose.ASSESSMENT,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            content: str = response.choices[0].message.content or ""
            if not content.strip():
                raise ValueError("Empty LLM response content")
            return _parse_llm_response(content)
        except Exception as exc:
            logger.warning(
                "AssessmentAgent LLM call failed; falling back to string equivalence",
                extra={"error": str(exc), "question_type": question_type},
            )
            is_correct = _string_equivalence(student_answer, correct)
            return AssessmentResult(
                is_correct=is_correct,
                normalized_answer=student_answer.strip(),
                error_type=None if is_correct else "Unclassified",
                error_code=None if is_correct else "ERR-UNCLASSIFIED",
                feedback_level="correct" if is_correct else "major_error",
                partial_credit=1.0 if is_correct else 0.0,
                confidence=0.5,
                assessment_reasoning="llm_fallback:string_equivalence",
            )

    async def __call__(self, state: SessionState) -> SessionState:
        """LangGraph node entry. Reads `state['last_student_answer']` and
        updates `state['last_assessment']`."""
        answer = str(state.get("last_student_answer", ""))
        result = await self.evaluate(state, answer)
        state["last_assessment"] = result
        state["next_agent"] = "progress_tracker"
        return state


# Purpose marker so callers know this agent is COPPA-routed to Ollama.
ASSESSMENT_LLM_PURPOSE = LLMPurpose.ASSESSMENT
