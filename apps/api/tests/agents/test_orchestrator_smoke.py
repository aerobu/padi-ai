"""Phase-3 smoke tests for the SessionOrchestrator.

Doesn't exercise the real LLMs — verifies that the four agent stubs are
wired correctly and the state machine routes them per PRD § 3.2.
"""

from __future__ import annotations

import pytest

from src.agents.orchestrator import (
    SessionOrchestrator,
    route_after_assessment,
    route_after_progress_tracker,
)
from src.agents.state import SessionState


@pytest.mark.unit
async def test_start_session_emits_a_question():
    orch = SessionOrchestrator()
    state = await orch.start_session(
        student_id="stu_1",
        session_id="sess_1",
        learning_plan_id="lp_1",
        current_skill_id="4.NF.A.1",
    )
    assert state["current_question"] is not None
    assert state["current_question"]["question_id"]
    assert state["session_complete"] is False


@pytest.mark.unit
async def test_correct_answer_triggers_progress_tracker_then_qgen():
    orch = SessionOrchestrator()
    state = await orch.start_session(
        student_id="stu_1",
        session_id="sess_1",
        learning_plan_id="lp_1",
        current_skill_id="4.NF.A.1",
    )
    correct = state["current_question"]["correct_answer"]
    first_qid = state["current_question"]["question_id"]
    state = await orch.submit_answer(state, correct)
    # progress_tracker bumped the counter, qgen swapped in a new question
    assert state["questions_answered"] == 1
    assert state["questions_correct"] == 1
    assert state["current_question"]["question_id"] != first_qid


@pytest.mark.unit
async def test_wrong_answer_routes_to_tutor():
    orch = SessionOrchestrator()
    state = await orch.start_session(
        student_id="stu_1",
        session_id="sess_1",
        learning_plan_id="lp_1",
        current_skill_id="4.NF.A.1",
    )
    state = await orch.submit_answer(state, "Z")  # wrong by construction
    assert "last_hint" in state  # tutor ran
    assert state["next_agent"] == "await_answer"
    # progress_tracker should NOT have advanced the counter yet
    assert state["questions_answered"] == 0


@pytest.mark.unit
async def test_three_wrong_attempts_advances_past_question():
    orch = SessionOrchestrator()
    state = await orch.start_session(
        student_id="stu_1",
        session_id="sess_1",
        learning_plan_id="lp_1",
        current_skill_id="4.NF.A.1",
    )
    first_qid = state["current_question"]["question_id"]
    for _ in range(3):
        state = await orch.submit_answer(state, "Z")
    # After 3rd wrong attempt the tracker should have advanced to a new question
    assert state["questions_answered"] == 1
    assert state["current_question"]["question_id"] != first_qid


@pytest.mark.unit
async def test_session_ends_after_ten_questions():
    orch = SessionOrchestrator()
    state = await orch.start_session(
        student_id="stu_1",
        session_id="sess_1",
        learning_plan_id="lp_1",
        current_skill_id="4.NF.A.1",
    )
    for _ in range(10):
        correct = state["current_question"]["correct_answer"]
        state = await orch.submit_answer(state, correct)
    assert state["session_complete"] is True
    assert state["next_agent"] == "end"


@pytest.mark.unit
def test_route_after_assessment_routes_to_tutor_on_high_frustration():
    state: SessionState = {  # type: ignore[typeddict-item]
        "frustration_score": 8.5,
        "session_complete": False,
        "last_assessment": {"is_correct": True},  # would normally → progress
    }
    assert route_after_assessment(state) == "tutor"


@pytest.mark.unit
def test_route_after_progress_tracker_ends_on_complete_flag():
    state: SessionState = {  # type: ignore[typeddict-item]
        "session_complete": True,
        "questions_answered": 3,
    }
    assert route_after_progress_tracker(state) == "end"
