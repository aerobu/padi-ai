"""Tutor Agent — Socratic hints with Flesch-Kincaid validation and frustration tracking.

Phase 4-B: Real LLM-backed hint delivery with a 3-attempt retry loop for
FK grade level (≤ 5.5) and banned-phrase checking. Updates frustration_score,
hints_used, and tutor_context. Routes through LLMClient(purpose=STUDENT_TUTORING)
which is COPPA-locked to local Ollama.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import textstat

from src.agents.state import SessionState
from src.clients.llm_client import LLMClient, LLMPurpose, get_llm_client

logger = logging.getLogger(__name__)


# ============================================================================
# Module-level constants
# ============================================================================

BANNED_PHRASES: list[str] = [
    "the answer is",
    "the correct answer is",
    "the solution is",
    "simply",
    "just do",
    "obviously",
    "easy",
    "trivial",
    "it's simple",
    "you just",
]

MAX_FK_GRADE: float = 5.5
MAX_RETRIES: int = 3


# ============================================================================
# Validators (inline)
# ============================================================================


def _word_count_ok(text: str) -> bool:
    """Check that response is ≤75 words."""
    return len(text.split()) <= 75


def _find_banned_phrases(text: str) -> list[str]:
    """Return list of banned phrases found in text (case-insensitive)."""
    lower = text.lower()
    return [phrase for phrase in BANNED_PHRASES if phrase in lower]


def _fk_grade_ok(text: str) -> bool:
    """Check that Flesch-Kincaid grade is ≤ 5.5."""
    return textstat.flesch_kincaid_grade(text) <= MAX_FK_GRADE


# ============================================================================
# Fallback hints (FK-safe, deterministic)
# ============================================================================


def _canned_hint(hint_level: int) -> str:
    """Deterministic fallback hints that pass all validation constraints."""
    if hint_level <= 1:
        return "Let's look at the numbers again. What is the question asking?"
    if hint_level == 2:
        return "Break it down step by step. Which math operation fits here?"
    return "Here is a hint: use the same steps, just with new numbers."


# ============================================================================
# Frustration scoring (pure function, exported for testing)
# ============================================================================


def compute_frustration_score(state: SessionState) -> float:
    """Compute frustration score from session signals.

    Formula: min(10.0, consecutive_wrong * 2.0 + attempt_count * 0.5 + hints_used * 0.3)

    Hits > 7.0 routing threshold at:
    - 4 consecutive wrong alone (8.0)
    - 3 consecutive wrong + 2 attempts + 3 hints (6.0 + 1.0 + 0.9 = 7.9)
    """
    consecutive_wrong = float(state.get("consecutive_wrong", 0))
    attempt_count = float(state.get("attempt_count", 0))
    hints_used = float(state.get("hints_used", 0))
    return min(10.0, consecutive_wrong * 2.0 + attempt_count * 0.5 + hints_used * 0.3)


# ============================================================================
# LLM prompt builders
# ============================================================================


def _build_system_prompt() -> str:
    """System prompt for the LLM-backed hint delivery."""
    return """You are an experienced Grade 4 math tutor for PADI.AI, an adaptive tutoring system for Oregon students aged 9–10.

AUDIENCE: Your student is 9–10 years old. Use short sentences and common words (Flesch-Kincaid grade ≤ 5.5). Never use words a typical 4th grader would not know.

HINT LEVELS — deliver the level specified in the user prompt:
- Level 1 (gentle nudge): Ask a single guiding question about the problem setup. Do not reference any operation or step yet.
- Level 2 (directed attention): Point the student's attention at the key operation or step without solving it.
- Level 3+ (near-reveal): Provide a worked example with different numbers, then invite the student to try the same approach.

EXPLANATION STYLE — adapt based on the style in the user prompt:
- step_by_step: sequential, numbered order
- visual: spatial language (above, below, left, groups)
- analogy: real-world comparison familiar to a 9-year-old
- auto: choose whichever style fits the question type best

BANNED PHRASES (case-insensitive — never use these):
"the answer is", "the correct answer is", "the solution is", "simply", "just do", "obviously", "easy", "trivial", "it's simple", "you just"

RULES:
1. Never reveal the answer directly, not even partially.
2. Keep hint_text to 75 words or fewer.
3. hint_text must be Flesch-Kincaid grade ≤ 5.5.
4. The "reasoning" field is for internal audit only — never shown to the student.

RESPONSE FORMAT — respond with ONLY a valid JSON object:
{
  "hint_text": "<string ≤ 75 words, grade 4 reading level, guides without revealing>",
  "reasoning": "<1-2 sentences of internal reasoning — never shown to student>"
}

Do not include any text outside the JSON object."""


def _build_user_prompt(
    question_text: str,
    correct_steps: list[str],
    question_type: str,
    error_code: Optional[str],
    error_type: Optional[str],
    hint_level: int,
    explanation_style: str,
    tutor_context: list[dict],
) -> str:
    """Build user prompt for the LLM hint delivery."""
    steps_str = "\n".join(correct_steps) if correct_steps else "(none provided)"

    diagnosis = ""
    if error_code:
        diagnosis = f"Diagnosed error: {error_code} — {error_type}\n"

    context_str = ""
    if tutor_context:
        context_lines = [
            f"  {i + 1}. [hint_level={e.get('hint_level', '?')}] {e.get('hint_text', '')}"
            for i, e in enumerate(tutor_context)
        ]
        context_str = "Prior hints in this session (do not repeat):\n" + "\n".join(
            context_lines
        )

    return f"""Question: {question_text}
Question type: {question_type}
Solution steps (do not reveal): {steps_str}
{diagnosis}Hint level requested: {hint_level}
Explanation style: {explanation_style}
{context_str}

Deliver a Hint Level {hint_level} hint in JSON format."""


def _parse_hint_text(content: str) -> str:
    """Parse and extract hint_text from LLM JSON response.

    Raises: json.JSONDecodeError or ValueError if invalid or empty.
    """
    data = json.loads(content)
    hint_text = str(data.get("hint_text", "")).strip()
    if not hint_text:
        raise ValueError("Empty hint_text in LLM response")
    return hint_text


# ============================================================================
# Tutor Agent class
# ============================================================================


class TutorAgent:
    """Deliver grade-appropriate, validated hints using LLM with retry loop."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client or get_llm_client()

    async def deliver_hint(self, state: SessionState, hint_level: int) -> str:
        """Return a validated hint string via LLM with 3-attempt retry loop.

        Falls back to a deterministic canned hint on any LLM failure or
        all retries exhausted.
        """
        question = state.get("current_question") or {}
        last_assessment = state.get("last_assessment") or {}

        messages: list[dict[str, str]] = [
            {"role": "system", "content": _build_system_prompt()},
            {
                "role": "user",
                "content": _build_user_prompt(
                    question_text=str(question.get("question_text", "")),
                    correct_steps=list(question.get("solution_steps") or []),
                    question_type=str(question.get("question_type", "numeric")),
                    error_code=last_assessment.get("error_code"),
                    error_type=last_assessment.get("error_type"),
                    hint_level=hint_level,
                    explanation_style=str(state.get("preferred_explanation_style") or "auto"),
                    tutor_context=list(state.get("tutor_context") or []),
                ),
            },
        ]

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.llm_client.acomplete(
                    messages,
                    purpose=LLMPurpose.STUDENT_TUTORING,
                    temperature=0.7,
                    response_format={"type": "json_object"},
                )
                content: str = response.choices[0].message.content or ""
                if not content.strip():
                    raise ValueError("Empty LLM response")
                hint_text = _parse_hint_text(content)
            except Exception as exc:
                logger.warning(
                    "TutorAgent LLM call failed on attempt %d; falling back to canned hint",
                    attempt + 1,
                    extra={"error": str(exc), "hint_level": hint_level},
                )
                return _canned_hint(hint_level)

            # Validate the hint text against all constraints
            issues: list[str] = []
            if not _word_count_ok(hint_text):
                word_count = len(hint_text.split())
                issues.append(
                    f"Response was {word_count} words. Keep it under 75 words."
                )
            if banned := _find_banned_phrases(hint_text):
                issues.append(
                    f"Remove these phrases: {banned}. Never reveal the answer directly."
                )
            if not _fk_grade_ok(hint_text):
                grade = textstat.flesch_kincaid_grade(hint_text)
                issues.append(
                    f"Reading level too high (grade {grade:.1f}). Use shorter sentences "
                    "and simpler words for Grade 4 students."
                )

            if not issues:
                return hint_text

            # Append correction request and retry
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": f"Revision needed: {' '.join(issues)} Please rewrite.",
                }
            )

        # All retries exhausted
        logger.warning(
            "TutorAgent: all %d retries exhausted; falling back to canned hint",
            MAX_RETRIES,
            extra={"hint_level": hint_level},
        )
        return _canned_hint(hint_level)

    async def __call__(self, state: SessionState) -> SessionState:
        """LangGraph node: deliver hint and update session state.

        Reads:
        - attempt_count → hint_level
        - current_question, last_assessment, preferred_explanation_style, tutor_context

        Writes:
        - last_hint
        - hints_used (increment)
        - tutor_context (append, keep last 3)
        - frustration_score (compute)
        - next_agent (set to "await_answer")
        """
        hint_level = max(1, int(state.get("attempt_count", 1)))
        hint_text = await self.deliver_hint(state, hint_level=hint_level)

        # 1. Write the hint
        state["last_hint"] = hint_text

        # 2. Increment hints used (before frustration score computation)
        state["hints_used"] = state.get("hints_used", 0) + 1

        # 3. Append to tutor context (keep last 3)
        question = state.get("current_question") or {}
        last_assessment = state.get("last_assessment") or {}
        entry: dict[str, object] = {
            "question_id": question.get("question_id", ""),
            "hint_level": hint_level,
            "hint_text": hint_text,
            "error_code": last_assessment.get("error_code"),
        }
        tutor_context = list(state.get("tutor_context") or [])
        tutor_context.append(entry)
        state["tutor_context"] = tutor_context[-3:]

        # 4. Update frustration score
        state["frustration_score"] = compute_frustration_score(state)

        # 5. Route to await_answer
        state["next_agent"] = "await_answer"

        return state


# Purpose marker so callers know this agent is COPPA-routed to Ollama.
TUTOR_LLM_PURPOSE = LLMPurpose.STUDENT_TUTORING
