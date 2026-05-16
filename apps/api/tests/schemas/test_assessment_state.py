"""Round-trip tests for the typed AssessmentRedisState (fix C-1)."""

from __future__ import annotations

import pytest

from src.schemas.internal.assessment_state import AssessmentRedisState


@pytest.mark.unit
def test_session_and_student_persist_through_redis_payload():
    state = AssessmentRedisState(
        assessment_id="a1",
        session_id="s1",
        student_id="stu_1",
        theta=0.42,
        questions_answered=3,
        covered_standards={"4.NF.A.1": 2},
        question_pool_size=120,
    )
    payload = state.to_redis_payload()
    assert payload["session_id"] == "s1"
    assert payload["student_id"] == "stu_1"

    restored = AssessmentRedisState.from_redis_payload(payload)
    assert restored.assessment_id == "a1"
    assert restored.session_id == "s1"
    assert restored.student_id == "stu_1"
    assert restored.theta == pytest.approx(0.42)
    assert restored.questions_answered == 3
    assert restored.covered_standards == {"4.NF.A.1": 2}


@pytest.mark.unit
def test_missing_required_field_raises():
    with pytest.raises(Exception):
        AssessmentRedisState(assessment_id="a1", session_id="s1")  # type: ignore[call-arg]
