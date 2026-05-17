"""Tests for the Assessment Agent — evaluates student answers and classifies errors.

Phase 4-A: Real LLM-backed evaluator with 15-code Grade 4 error taxonomy.
Tests cover: correct answers, each error code, partial credit, LLM fallback, confidence bounds.
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.agents.assessment_agent import AssessmentAgent
from src.agents.state import SessionState, QuestionContext, AssessmentResult


def _make_mock_client(json_payload: dict) -> AsyncMock:
    """Return an AsyncMock LLMClient whose acomplete() returns json_payload as content."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(json_payload)
    mock_client = AsyncMock()
    mock_client.acomplete = AsyncMock(return_value=mock_response)
    return mock_client


def _make_state(
    question_type: str = "multiple_choice",
    correct_answer: str = "42",
    question_text: str = "What is 6 × 7?",
    attempt_count: int = 1,
) -> SessionState:
    """Build a minimal SessionState for testing."""
    return SessionState(
        student_id="stu-1",
        session_id="sess-1",
        current_question=QuestionContext(
            question_id="q-1",
            skill_id="4.OA.A.2",
            question_text=question_text,
            question_type=question_type,  # type: ignore[arg-type]
            correct_answer=correct_answer,
        ),
        attempt_count=attempt_count,
    )


# ============================================================================
# GROUP A: Correct Answers (5 tests)
# ============================================================================


class TestCorrectAnswers:
    """Test correct answer scenarios."""

    @pytest.mark.asyncio
    async def test_correct_multiple_choice(self):
        """Correct multiple choice answer."""
        mock_client = _make_mock_client({
            "is_correct": True,
            "normalized_answer": "B",
            "error_code": None,
            "error_type": None,
            "partial_credit": 1.0,
            "confidence": 0.95,
            "feedback_level": "correct",
            "assessment_reasoning": "Answer matches exactly.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_type="multiple_choice", correct_answer="B")
        result = await agent.evaluate(state, "B")
        assert result["is_correct"] is True
        assert result["feedback_level"] == "correct"
        assert result["error_code"] is None
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_correct_numeric(self):
        """Correct numeric answer."""
        mock_client = _make_mock_client({
            "is_correct": True,
            "normalized_answer": "42",
            "error_code": None,
            "error_type": None,
            "partial_credit": 1.0,
            "confidence": 0.98,
            "feedback_level": "correct",
            "assessment_reasoning": "Numeric match.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_type="numeric", correct_answer="42")
        result = await agent.evaluate(state, "42")
        assert result["is_correct"] is True
        assert result["partial_credit"] == 1.0
        assert result["error_type"] is None

    @pytest.mark.asyncio
    async def test_correct_multi_step_fully_correct(self):
        """Correct multi-step answer with full credit."""
        mock_client = _make_mock_client({
            "is_correct": True,
            "normalized_answer": "32",
            "error_code": None,
            "error_type": None,
            "partial_credit": 1.0,
            "confidence": 0.92,
            "feedback_level": "correct",
            "assessment_reasoning": "All steps executed correctly.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_type="multi_step", correct_answer="32")
        result = await agent.evaluate(state, "32")
        assert result["is_correct"] is True
        assert result["partial_credit"] == 1.0

    @pytest.mark.asyncio
    async def test_correct_case_insensitive(self):
        """Case-insensitive matching of correct answer."""
        mock_client = _make_mock_client({
            "is_correct": True,
            "normalized_answer": "b",
            "error_code": None,
            "error_type": None,
            "partial_credit": 1.0,
            "confidence": 0.90,
            "feedback_level": "correct",
            "assessment_reasoning": "Case-insensitive match.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_type="multiple_choice", correct_answer="B")
        result = await agent.evaluate(state, "b")
        assert result["is_correct"] is True

    @pytest.mark.asyncio
    async def test_correct_whitespace_padded(self):
        """Whitespace-padded correct answer."""
        mock_client = _make_mock_client({
            "is_correct": True,
            "normalized_answer": "42",
            "error_code": None,
            "error_type": None,
            "partial_credit": 1.0,
            "confidence": 0.93,
            "feedback_level": "correct",
            "assessment_reasoning": "Whitespace handled.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_type="numeric", correct_answer="42")
        result = await agent.evaluate(state, "  42  ")
        assert result["is_correct"] is True
        assert result["normalized_answer"] == "42"


# ============================================================================
# GROUP B: Error Taxonomy (15 tests, one per error code)
# ============================================================================


class TestErrorTaxonomy:
    """Test each of the 15 error codes with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_error_place_value(self):
        """ERR-PLACE-VALUE: misunderstood positional notation."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "394",
            "error_code": "ERR-PLACE-VALUE",
            "error_type": "Place value",
            "partial_credit": 0.0,
            "confidence": 0.88,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student treated tens place as if subtracting 100 instead of 10.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 304 - 10?", correct_answer="294")
        result = await agent.evaluate(state, "394")
        assert result["error_code"] == "ERR-PLACE-VALUE"
        assert result["is_correct"] is False

    @pytest.mark.asyncio
    async def test_error_carrying(self):
        """ERR-CARRYING: forgot to carry in addition."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "113",
            "error_code": "ERR-CARRYING",
            "error_type": "Carrying",
            "partial_credit": 0.0,
            "confidence": 0.91,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student did not carry the 1 from 8+5=13.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 78 + 45?", correct_answer="123")
        result = await agent.evaluate(state, "113")
        assert result["error_code"] == "ERR-CARRYING"

    @pytest.mark.asyncio
    async def test_error_mult_fact(self):
        """ERR-MULT-FACT: wrong multiplication fact recall."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "54",
            "error_code": "ERR-MULT-FACT",
            "error_type": "Multiplication fact",
            "partial_credit": 0.0,
            "confidence": 0.87,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student recalled 7 × 8 = 54 instead of 56.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 7 × 8?", correct_answer="56")
        result = await agent.evaluate(state, "54")
        assert result["error_code"] == "ERR-MULT-FACT"

    @pytest.mark.asyncio
    async def test_error_div_fact(self):
        """ERR-DIV-FACT: wrong division fact."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "6",
            "error_code": "ERR-DIV-FACT",
            "error_type": "Division fact",
            "partial_credit": 0.0,
            "confidence": 0.84,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student recalled 63 ÷ 9 = 6 instead of 7.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 63 ÷ 9?", correct_answer="7")
        result = await agent.evaluate(state, "6")
        assert result["error_code"] == "ERR-DIV-FACT"

    @pytest.mark.asyncio
    async def test_error_op_select(self):
        """ERR-OP-SELECT: applied wrong operation."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "9",
            "error_code": "ERR-OP-SELECT",
            "error_type": "Operation selection",
            "partial_credit": 0.0,
            "confidence": 0.89,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student added 3 + 6 instead of multiplying 3 × 6.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_text="Sam has 3 bags with 6 apples each. How many apples total?",
            correct_answer="18",
        )
        result = await agent.evaluate(state, "9")
        assert result["error_code"] == "ERR-OP-SELECT"

    @pytest.mark.asyncio
    async def test_error_fraction_eq(self):
        """ERR-FRACTION-EQ: failed to find common denominator."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "2/5",
            "error_code": "ERR-FRACTION-EQ",
            "error_type": "Fraction equivalence",
            "partial_credit": 0.0,
            "confidence": 0.85,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student added numerators and denominators separately.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 1/2 + 1/3?", correct_answer="5/6")
        result = await agent.evaluate(state, "2/5")
        assert result["error_code"] == "ERR-FRACTION-EQ"

    @pytest.mark.asyncio
    async def test_error_fraction_part(self):
        """ERR-FRACTION-PART: confused numerator/denominator."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "3",
            "error_code": "ERR-FRACTION-PART",
            "error_type": "Fraction parts",
            "partial_credit": 0.0,
            "confidence": 0.86,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student gave numerator instead of denominator.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_text="What is the denominator of 3/4?",
            correct_answer="4",
        )
        result = await agent.evaluate(state, "3")
        assert result["error_code"] == "ERR-FRACTION-PART"

    @pytest.mark.asyncio
    async def test_error_unit_convert(self):
        """ERR-UNIT-CONVERT: wrong conversion magnitude."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "3",
            "error_code": "ERR-UNIT-CONVERT",
            "error_type": "Unit conversion",
            "partial_credit": 0.0,
            "confidence": 0.82,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student did not apply the conversion factor (12 inches/foot).",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="3 feet = ? inches", correct_answer="36")
        result = await agent.evaluate(state, "3")
        assert result["error_code"] == "ERR-UNIT-CONVERT"

    @pytest.mark.asyncio
    async def test_error_rounding(self):
        """ERR-ROUNDING: rounded to wrong place value."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "350",
            "error_code": "ERR-ROUNDING",
            "error_type": "Rounding",
            "partial_credit": 0.0,
            "confidence": 0.88,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student rounded 347 to nearest tens (350) instead of hundreds (300).",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_text="Round 347 to the nearest hundred.",
            correct_answer="300",
        )
        result = await agent.evaluate(state, "350")
        assert result["error_code"] == "ERR-ROUNDING"

    @pytest.mark.asyncio
    async def test_error_comparison(self):
        """ERR-COMPARISON: wrong inequality or ordering."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "2/3",
            "error_code": "ERR-COMPARISON",
            "error_type": "Comparison",
            "partial_credit": 0.0,
            "confidence": 0.83,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student chose the lesser fraction.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_text="Which is greater: 3/4 or 2/3?",
            correct_answer="3/4",
        )
        result = await agent.evaluate(state, "2/3")
        assert result["error_code"] == "ERR-COMPARISON"

    @pytest.mark.asyncio
    async def test_error_partial_proc(self):
        """ERR-PARTIAL-PROC: stopped calculation mid-way."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "4 × 8",
            "error_code": "ERR-PARTIAL-PROC",
            "error_type": "Partial procedure",
            "partial_credit": 0.0,
            "confidence": 0.80,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student set up correctly but left answer as expression.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_text="Solve: 4 × (3 + 5)",
            correct_answer="32",
        )
        result = await agent.evaluate(state, "4 × 8")
        assert result["error_code"] == "ERR-PARTIAL-PROC"

    @pytest.mark.asyncio
    async def test_error_transcription(self):
        """ERR-TRANSCRIPTION: copied digit incorrectly."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "371",
            "error_code": "ERR-TRANSCRIPTION",
            "error_type": "Transcription",
            "partial_credit": 0.0,
            "confidence": 0.81,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student transcribed 3 as 2 in the first digit.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 236 + 145?", correct_answer="381")
        result = await agent.evaluate(state, "371")
        assert result["error_code"] == "ERR-TRANSCRIPTION"

    @pytest.mark.asyncio
    async def test_error_conceptual(self):
        """ERR-CONCEPTUAL: correct procedure, wrong concept."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "20",
            "error_code": "ERR-CONCEPTUAL",
            "error_type": "Conceptual",
            "partial_credit": 0.0,
            "confidence": 0.84,
            "feedback_level": "conceptual_gap",
            "assessment_reasoning": "Student added dimensions instead of multiplying for area.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_text="What is the area of a 4×6 rectangle?",
            correct_answer="24",
        )
        result = await agent.evaluate(state, "20")
        assert result["error_code"] == "ERR-CONCEPTUAL"
        assert result["feedback_level"] == "conceptual_gap"

    @pytest.mark.asyncio
    async def test_error_computation(self):
        """ERR-COMPUTATION: general arithmetic slip."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "56",
            "error_code": "ERR-COMPUTATION",
            "error_type": "Arithmetic error",
            "partial_credit": 0.0,
            "confidence": 0.79,
            "feedback_level": "minor_error",
            "assessment_reasoning": "Student made a computational slip in 15 × 4.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 15 × 4?", correct_answer="60")
        result = await agent.evaluate(state, "56")
        assert result["error_code"] == "ERR-COMPUTATION"

    @pytest.mark.asyncio
    async def test_error_unclassified(self):
        """ERR-UNCLASSIFIED: cannot determine error type."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "",
            "error_code": "ERR-UNCLASSIFIED",
            "error_type": "Unclassified",
            "partial_credit": 0.0,
            "confidence": 0.50,
            "feedback_level": "major_error",
            "assessment_reasoning": "No answer provided.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(question_text="What is 2 + 2?", correct_answer="4")
        result = await agent.evaluate(state, "")
        assert result["error_code"] == "ERR-UNCLASSIFIED"


# ============================================================================
# GROUP C: Partial Credit (3 tests)
# ============================================================================


class TestPartialCredit:
    """Test partial credit scenarios for multi_step questions."""

    @pytest.mark.asyncio
    async def test_partial_credit_multi_step_half(self):
        """Multi-step question with setup correct but arithmetic wrong (0.5)."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "30",
            "error_code": "ERR-COMPUTATION",
            "error_type": "Arithmetic error",
            "partial_credit": 0.5,
            "confidence": 0.77,
            "feedback_level": "minor_error",
            "assessment_reasoning": "Setup 5 × 6 is correct, but student computed as 30 instead of 32.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_type="multi_step",
            question_text="Solve: 4 + (5 × 6) - 2",
            correct_answer="32",
        )
        result = await agent.evaluate(state, "30")
        assert result["partial_credit"] == 0.5

    @pytest.mark.asyncio
    async def test_partial_credit_multi_step_full(self):
        """Multi-step question fully correct (1.0)."""
        mock_client = _make_mock_client({
            "is_correct": True,
            "normalized_answer": "32",
            "error_code": None,
            "error_type": None,
            "partial_credit": 1.0,
            "confidence": 0.96,
            "feedback_level": "correct",
            "assessment_reasoning": "All steps executed correctly.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_type="multi_step",
            question_text="Solve: 4 + (5 × 6) - 2",
            correct_answer="32",
        )
        result = await agent.evaluate(state, "32")
        assert result["partial_credit"] == 1.0

    @pytest.mark.asyncio
    async def test_partial_credit_multi_step_zero(self):
        """Multi-step question completely wrong (0.0)."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "10",
            "error_code": "ERR-OP-SELECT",
            "error_type": "Operation selection",
            "partial_credit": 0.0,
            "confidence": 0.82,
            "feedback_level": "major_error",
            "assessment_reasoning": "Student chose wrong operations entirely.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(
            question_type="multi_step",
            question_text="Solve: 4 + (5 × 6) - 2",
            correct_answer="32",
        )
        result = await agent.evaluate(state, "10")
        assert result["partial_credit"] == 0.0


# ============================================================================
# GROUP D: LLM Fallback (5 tests)
# ============================================================================


class TestLLMFallback:
    """Test fallback behavior when LLM call fails."""

    @pytest.mark.asyncio
    async def test_fallback_on_llm_exception(self):
        """LLM raises exception — fall back to string equivalence."""
        mock_client = AsyncMock()
        mock_client.acomplete = AsyncMock(side_effect=Exception("Connection refused"))
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "wrong")
        assert result["error_code"] == "ERR-UNCLASSIFIED"
        assert result["confidence"] == 0.5
        assert result["is_correct"] is False

    @pytest.mark.asyncio
    async def test_fallback_on_json_parse_error(self):
        """LLM returns non-JSON content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not JSON at all"
        mock_client = AsyncMock()
        mock_client.acomplete = AsyncMock(return_value=mock_response)
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "wrong")
        assert result["error_code"] == "ERR-UNCLASSIFIED"
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_fallback_on_empty_content(self):
        """LLM returns empty string content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_client = AsyncMock()
        mock_client.acomplete = AsyncMock(return_value=mock_response)
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "wrong")
        assert result["error_code"] == "ERR-UNCLASSIFIED"
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_fallback_on_none_content(self):
        """LLM returns None for content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client = AsyncMock()
        mock_client.acomplete = AsyncMock(return_value=mock_response)
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "wrong")
        assert result["error_code"] == "ERR-UNCLASSIFIED"
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_fallback_correct_answer_still_recognized(self):
        """LLM call fails but correct answer is still recognized via fallback."""
        mock_client = AsyncMock()
        mock_client.acomplete = AsyncMock(side_effect=Exception("timeout"))
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "42")
        assert result["is_correct"] is True
        assert result["confidence"] == 0.5
        assert result["error_code"] is None


# ============================================================================
# GROUP E: Confidence Bounds (3 tests)
# ============================================================================


class TestConfidenceBounds:
    """Test confidence clamping to [0.0, 1.0]."""

    @pytest.mark.asyncio
    async def test_confidence_clamped_above_one(self):
        """LLM returns confidence > 1.0 — clamped to 1.0."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "99",
            "error_code": "ERR-COMPUTATION",
            "error_type": "Arithmetic error",
            "partial_credit": 0.0,
            "confidence": 1.5,
            "feedback_level": "major_error",
            "assessment_reasoning": "LLM returned out-of-range confidence.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "99")
        assert result["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_confidence_clamped_below_zero(self):
        """LLM returns confidence < 0.0 — clamped to 0.0."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "99",
            "error_code": "ERR-COMPUTATION",
            "error_type": "Arithmetic error",
            "partial_credit": 0.0,
            "confidence": -0.3,
            "feedback_level": "major_error",
            "assessment_reasoning": "LLM returned negative confidence.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "99")
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_confidence_exactly_zero_allowed(self):
        """Confidence exactly 0.0 is valid."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "99",
            "error_code": "ERR-UNCLASSIFIED",
            "error_type": "Unclassified",
            "partial_credit": 0.0,
            "confidence": 0.0,
            "feedback_level": "major_error",
            "assessment_reasoning": "Complete uncertainty.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        result = await agent.evaluate(state, "99")
        assert result["confidence"] == 0.0


# ============================================================================
# GROUP F: LangGraph __call__ Node (2 tests)
# ============================================================================


class TestCallNode:
    """Test the LangGraph node entry (__call__)."""

    @pytest.mark.asyncio
    async def test_call_populates_last_assessment(self):
        """__call__ reads last_student_answer and populates last_assessment."""
        mock_client = _make_mock_client({
            "is_correct": True,
            "normalized_answer": "42",
            "error_code": None,
            "error_type": None,
            "partial_credit": 1.0,
            "confidence": 0.95,
            "feedback_level": "correct",
            "assessment_reasoning": "Correct.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        state["last_student_answer"] = "42"
        result_state = await agent(state)
        assert "last_assessment" in result_state
        assert result_state["last_assessment"]["is_correct"] is True
        assert result_state["last_assessment"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_call_sets_next_agent_to_progress_tracker(self):
        """__call__ sets next_agent to 'progress_tracker'."""
        mock_client = _make_mock_client({
            "is_correct": False,
            "normalized_answer": "99",
            "error_code": "ERR-COMPUTATION",
            "error_type": "Arithmetic error",
            "partial_credit": 0.0,
            "confidence": 0.6,
            "feedback_level": "major_error",
            "assessment_reasoning": "Wrong answer.",
        })
        agent = AssessmentAgent(llm_client=mock_client)
        state = _make_state(correct_answer="42")
        state["last_student_answer"] = "99"
        result_state = await agent(state)
        assert result_state["next_agent"] == "progress_tracker"
