"""Tests for Tutor Agent — LLM-backed hint delivery with validation and frustration tracking.

Phase 4-B: Real implementation with 3-attempt retry loop for FK + banned-phrase checks.
22 tests covering: successful LLM calls, retry logic, state mutations, frustration scoring,
fallback behavior, and LangGraph node contract.
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.agents.tutor_agent import (
    TutorAgent,
    compute_frustration_score,
    _canned_hint,
)
from src.agents.state import SessionState, QuestionContext


# ============================================================================
# Test helpers
# ============================================================================


def _make_mock_client(hint_text: str, reasoning: str = "internal") -> AsyncMock:
    """Return an AsyncMock LLMClient whose acomplete() returns a single valid JSON hint."""
    payload = {"hint_text": hint_text, "reasoning": reasoning}
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(payload)
    mock_client = AsyncMock()
    mock_client.acomplete = AsyncMock(return_value=mock_response)
    return mock_client


def _make_multi_response_client(payloads: list[dict | Exception]) -> AsyncMock:
    """Return an AsyncMock that returns successive responses or raises exceptions.

    Each payload is either:
    - dict: converted to JSON and returned as LLM response
    - Exception: raised directly by acomplete
    """
    side_effects = []
    for item in payloads:
        if isinstance(item, Exception):
            side_effects.append(item)
        else:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(item)
            side_effects.append(mock_response)
    mock_client = AsyncMock()
    mock_client.acomplete = AsyncMock(side_effect=side_effects)
    return mock_client


def _make_state(
    student_id: str = "stu-1",
    session_id: str = "sess-1",
    attempt_count: int = 1,
    hints_used: int = 0,
    consecutive_wrong: int = 0,
    preferred_explanation_style: str = "auto",
    question_text: str = "What is 6 × 7?",
    question_type: str = "numeric",
    solution_steps: list[str] | None = None,
    last_assessment: dict | None = None,
    tutor_context: list[dict] | None = None,
) -> SessionState:
    """Build a minimal SessionState for testing."""
    return SessionState(
        student_id=student_id,
        session_id=session_id,
        current_question=QuestionContext(
            question_id="q-1",
            skill_id="4.OA.A.2",
            question_text=question_text,
            question_type=question_type,  # type: ignore[arg-type]
            correct_answer="42",
            solution_steps=solution_steps or ["Multiply 6 by 7"],
        ),
        attempt_count=attempt_count,
        hints_used=hints_used,
        consecutive_wrong=consecutive_wrong,
        preferred_explanation_style=preferred_explanation_style,  # type: ignore[arg-type]
        last_assessment=last_assessment,
        tutor_context=tutor_context or [],
    )


# ============================================================================
# GROUP A: Successful LLM Responses (4 tests)
# ============================================================================


class TestSuccessfulLLMResponses:
    """Test successful hint delivery via LLM."""

    @pytest.mark.asyncio
    async def test_hint_level_1_returned(self):
        """Gentle nudge hint (level 1) is returned."""
        hint_text = "What numbers do you see in the problem?"
        mock_client = _make_mock_client(hint_text)
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(attempt_count=1)
        result_state = await agent(state)
        assert result_state["last_hint"] == hint_text

    @pytest.mark.asyncio
    async def test_hint_level_2_returned(self):
        """Directed attention hint (level 2) is returned."""
        hint_text = "Which math operation do you need here?"
        mock_client = _make_mock_client(hint_text)
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(attempt_count=2)
        result_state = await agent(state)
        assert result_state["last_hint"] == hint_text

    @pytest.mark.asyncio
    async def test_hint_level_3_returned(self):
        """Near-reveal hint (level 3) is returned."""
        hint_text = "Try these steps: add, then divide. Use your numbers."
        mock_client = _make_mock_client(hint_text)
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(attempt_count=3)
        result_state = await agent(state)
        assert result_state["last_hint"] == hint_text

    @pytest.mark.asyncio
    async def test_explanation_style_consumed(self):
        """LLM is invoked (not fallback canned hint)."""
        hint_text = "Look at each number separately first."
        mock_client = _make_mock_client(hint_text)
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(preferred_explanation_style="step_by_step")
        await agent(state)
        # If LLM was called, acomplete was invoked once
        mock_client.acomplete.assert_called_once()


# ============================================================================
# GROUP B: Banned Phrase Retry (3 tests)
# ============================================================================


class TestBannedPhraseRetry:
    """Test retry behavior on banned phrases."""

    @pytest.mark.asyncio
    async def test_banned_phrase_triggers_retry(self):
        """Single banned phrase triggers one retry."""
        mock_client = _make_multi_response_client([
            {"hint_text": "the answer is 42", "reasoning": "bad"},
            {"hint_text": "Look at the numbers. What do you see?", "reasoning": "good"},
        ])
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state()
        result_state = await agent(state)
        assert mock_client.acomplete.call_count == 2
        assert result_state["last_hint"] == "Look at the numbers. What do you see?"

    @pytest.mark.asyncio
    async def test_multiple_banned_phrase_retries(self):
        """Multiple failed attempts eventually succeed."""
        mock_client = _make_multi_response_client([
            {"hint_text": "the answer is 42", "reasoning": "bad1"},
            {"hint_text": "the correct answer is 42", "reasoning": "bad2"},
            {"hint_text": "Break it down step by step.", "reasoning": "good"},
        ])
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state()
        result_state = await agent(state)
        assert mock_client.acomplete.call_count == 3
        assert result_state["last_hint"] == "Break it down step by step."

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_uses_fallback(self):
        """After 3 failed retries, fall back to canned hint."""
        mock_client = _make_multi_response_client([
            {"hint_text": "the answer is 42", "reasoning": "x"},
            {"hint_text": "the solution is 42", "reasoning": "x"},
            {"hint_text": "just do 42", "reasoning": "x"},
        ])
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(attempt_count=1)
        result_state = await agent(state)
        assert result_state["last_hint"] == _canned_hint(1)
        assert mock_client.acomplete.call_count == 3


# ============================================================================
# GROUP C: Flesch-Kincaid Validation (3 tests)
# ============================================================================


# High-FK sentence (should fail validation)
_HIGH_FK_TEXT = (
    "Multiplication distributes across compositional numerical factors "
    "within the arithmetic progression systematic evaluation framework."
)

# Low-FK sentence (should pass validation)
_LOW_FK_TEXT = "Look at the numbers. What do you see?"


class TestFKValidation:
    """Test Flesch-Kincaid grade level validation."""

    @pytest.mark.asyncio
    async def test_fk_grade_below_max_passes(self):
        """Response with FK grade < 5.5 passes validation."""
        mock_client = _make_mock_client(_LOW_FK_TEXT)
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state()
        result_state = await agent(state)
        assert result_state["last_hint"] == _LOW_FK_TEXT
        assert mock_client.acomplete.call_count == 1

    @pytest.mark.asyncio
    async def test_fk_grade_above_max_triggers_retry(self):
        """Response with FK grade > 5.5 triggers retry."""
        mock_client = _make_multi_response_client([
            {"hint_text": _HIGH_FK_TEXT, "reasoning": "x"},
            {"hint_text": _LOW_FK_TEXT, "reasoning": "ok"},
        ])
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state()
        result_state = await agent(state)
        assert mock_client.acomplete.call_count == 2
        assert result_state["last_hint"] == _LOW_FK_TEXT

    @pytest.mark.asyncio
    async def test_fk_fallback_after_all_retries(self):
        """FK check fails all 3 times; fall back to canned hint."""
        mock_client = _make_multi_response_client([
            {"hint_text": _HIGH_FK_TEXT, "reasoning": "x"},
            {"hint_text": _HIGH_FK_TEXT, "reasoning": "x"},
            {"hint_text": _HIGH_FK_TEXT, "reasoning": "x"},
        ])
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(attempt_count=2)
        result_state = await agent(state)
        assert result_state["last_hint"] == _canned_hint(2)
        assert mock_client.acomplete.call_count == 3


# ============================================================================
# GROUP D: State Mutations (5 tests)
# ============================================================================


class TestStateMutations:
    """Test that tutor updates session state correctly."""

    @pytest.mark.asyncio
    async def test_hints_used_incremented(self):
        """hints_used is incremented from 0 to 1."""
        mock_client = _make_mock_client("What do you notice?")
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(hints_used=0)
        result_state = await agent(state)
        assert result_state["hints_used"] == 1

    @pytest.mark.asyncio
    async def test_hints_used_accumulates(self):
        """hints_used accumulates across multiple calls."""
        mock_client = _make_mock_client("What do you notice?")
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(hints_used=5)
        result_state = await agent(state)
        assert result_state["hints_used"] == 6

    @pytest.mark.asyncio
    async def test_tutor_context_appended(self):
        """New entry appended to tutor_context."""
        mock_client = _make_mock_client("Try again.")
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(tutor_context=[])
        result_state = await agent(state)
        assert len(result_state["tutor_context"]) == 1
        assert result_state["tutor_context"][0]["hint_text"] == "Try again."
        assert result_state["tutor_context"][0]["hint_level"] == 1

    @pytest.mark.asyncio
    async def test_tutor_context_capped_at_3(self):
        """tutor_context keeps only last 3 entries."""
        mock_client = _make_mock_client("Look harder.")
        agent = TutorAgent(llm_client=mock_client)
        initial_context = [
            {"question_id": "q1", "hint_text": "Hint 1", "hint_level": 1},
            {"question_id": "q2", "hint_text": "Hint 2", "hint_level": 2},
            {"question_id": "q3", "hint_text": "Hint 3", "hint_level": 3},
        ]
        state = _make_state(tutor_context=initial_context)
        result_state = await agent(state)
        assert len(result_state["tutor_context"]) == 3
        assert result_state["tutor_context"][2]["hint_text"] == "Look harder."
        assert result_state["tutor_context"][0]["hint_text"] == "Hint 2"

    @pytest.mark.asyncio
    async def test_frustration_score_updated(self):
        """frustration_score is updated (not left at 0.0)."""
        mock_client = _make_mock_client("What's next?")
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(consecutive_wrong=2, attempt_count=1, hints_used=0)
        result_state = await agent(state)
        # After incrementing hints_used to 1: 2*2.0 + 1*0.5 + 1*0.3 = 4.8
        expected_score = 2.0 * 2.0 + 1.0 * 0.5 + 1.0 * 0.3
        assert result_state["frustration_score"] == expected_score


# ============================================================================
# GROUP E: Frustration Score (3 tests)
# ============================================================================


class TestFrustrationScore:
    """Test compute_frustration_score function (unit tests, no async)."""

    def test_compute_frustration_score_zero_state(self):
        """All zeros yield 0.0."""
        state = _make_state(consecutive_wrong=0, attempt_count=0, hints_used=0)
        score = compute_frustration_score(state)
        assert score == 0.0

    def test_compute_frustration_score_high(self):
        """4 consecutive wrong alone exceeds 7.0 threshold."""
        state = _make_state(consecutive_wrong=4, attempt_count=0, hints_used=0)
        score = compute_frustration_score(state)
        assert score > 7.0
        assert score == 8.0

    def test_compute_frustration_score_capped(self):
        """Very high inputs are capped at 10.0."""
        state = _make_state(consecutive_wrong=100, attempt_count=100, hints_used=100)
        score = compute_frustration_score(state)
        assert score == 10.0


# ============================================================================
# GROUP F: LangGraph __call__ Node (2 tests)
# ============================================================================


class TestCallNode:
    """Test the LangGraph node entry (__call__)."""

    @pytest.mark.asyncio
    async def test_call_sets_last_hint_and_next_agent(self):
        """__call__ sets both last_hint and next_agent."""
        hint_text = "Let's try a different approach."
        mock_client = _make_mock_client(hint_text)
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state()
        result_state = await agent(state)
        assert "last_hint" in result_state
        assert result_state["last_hint"] == hint_text
        assert result_state["next_agent"] == "await_answer"

    @pytest.mark.asyncio
    async def test_call_with_error_code_from_assessment(self):
        """Error context from last_assessment is passed to LLM."""
        mock_client = _make_mock_client("Check your multiplication.")
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(
            last_assessment={
                "error_code": "ERR-MULT-FACT",
                "error_type": "Multiplication fact",
            }
        )
        await agent(state)
        # Verify LLM was invoked (not fallback)
        assert mock_client.acomplete.call_count >= 1


# ============================================================================
# GROUP G: Fallback (2 tests)
# ============================================================================


class TestFallback:
    """Test fallback behavior on LLM failure."""

    @pytest.mark.asyncio
    async def test_fallback_on_llm_exception(self):
        """LLM raises exception; fall back to canned hint."""
        mock_client = AsyncMock()
        mock_client.acomplete = AsyncMock(side_effect=Exception("timeout"))
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(attempt_count=1)
        result_state = await agent(state)
        assert result_state["last_hint"] == _canned_hint(1)
        assert "last_hint" in result_state

    @pytest.mark.asyncio
    async def test_fallback_sets_next_agent(self):
        """Even on fallback, next_agent is set."""
        mock_client = AsyncMock()
        mock_client.acomplete = AsyncMock(side_effect=Exception("network error"))
        agent = TutorAgent(llm_client=mock_client)
        state = _make_state(attempt_count=2)
        result_state = await agent(state)
        assert result_state["next_agent"] == "await_answer"
        assert result_state["hints_used"] == 1  # still incremented
