"""
TDD tests for POST /sessions/{session_id}/answer authorization.

Task 1.6: ownership guard + fix Lesson/Module import refs.
The 403 ownership check must fire before any code that references
nonexistent session fields (question_ids, current_question_index).
"""
import pytest
from uuid import uuid4
from src.models.models import (
    User, Student, LearningPlan, PlanModule, PlanLesson, PracticeSession, Standard,
)


@pytest.mark.asyncio
async def test_session_answer_forbidden_for_non_owner(client, async_db_session):
    """A parent who does not own the session should receive 403."""
    parent_a = User(
        id="parent-a-session",
        auth0_id="auth0|a-session",
        role="parent",
        is_active=True,
        first_name="A",
        last_name="Parent",
    )
    parent_a.set_email("a-session@example.com")
    student_x = Student(
        id=str(uuid4()),
        parent_id="parent-a-session",
        grade_level=4,
        display_name="Child X",
        is_active=True,
    )
    from datetime import date
    plan = LearningPlan(
        id=str(uuid4()),
        student_id=student_x.id,
        track="on_track",
        status="active",
        total_modules=1,
        total_lessons=1,
        estimated_total_minutes=20,
        estimated_completion_date=date(2026, 12, 31),
    )
    module = PlanModule(
        id=str(uuid4()),
        plan_id=plan.id,
        standard_id="4.NBT.A.1",
        sequence_order=1,
        lesson_count=1,
        estimated_minutes=20,
    )
    lesson = PlanLesson(
        id=str(uuid4()),
        module_id=module.id,
        sequence_order=1,
        title="Test Lesson",
    )
    session_row = PracticeSession(
        id=str(uuid4()),
        lesson_id=lesson.id,
        student_id=student_x.id,
        standard_code="4.NBT.A.1",
        question_count=5,
    )
    standard = Standard(
        id="4.NBT.A.1",
        standard_code="4.NBT.A.1",
        grade_level=4,
        domain="NBT",
        title="Number and Operations in Base Ten",
        description="Recognize that in a multi-digit whole number, a digit represents ten times what it represents in the place to its right.",
        is_active=True,
    )
    # Insert in FK dependency order so constraints are satisfied
    async_db_session.add(standard)
    async_db_session.add(parent_a)
    await async_db_session.flush()
    async_db_session.add(student_x)
    await async_db_session.flush()
    async_db_session.add(plan)
    await async_db_session.flush()
    async_db_session.add(module)
    await async_db_session.flush()
    async_db_session.add(lesson)
    await async_db_session.flush()
    async_db_session.add(session_row)
    await async_db_session.flush()

    # The client fixture is authenticated as a DIFFERENT user (not parent_a),
    # so the ownership check should return 403.
    response = await client.post(
        f"/api/v1/sessions/{session_row.id}/answer",
        json={"answer": "4", "time_spent_ms": 1000},
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_session_answer_not_found_for_bogus_session(client, async_db_session):
    """A request for a nonexistent session should return 404."""
    response = await client.post(
        f"/api/v1/sessions/{uuid4()}/answer",
        json={"answer": "4", "time_spent_ms": 1000},
    )
    assert response.status_code == 404, response.text
