"""Task 2.1: integration test for the rewritten session-answer endpoint."""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import date
from src.models.models import (
    User, Student, LearningPlan, PlanModule, PlanLesson,
    PracticeSession, PracticeSessionQuestion, GeneratedQuestion,
    Standard, GenerationJob,
)


@pytest_asyncio.fixture
async def session_flow_seed(async_db_session):
    """Seed a complete session-answer scenario owned by the default client fixture parent."""
    # The default `client` fixture authenticates as sub "test-user-id".
    parent = User(
        id="test-user-id",
        auth0_id="auth0|test-flow",
        role="parent",
        is_active=True,
        first_name="T",
        last_name="U",
    )
    parent.set_email("t-flow@u.com")
    student = Student(
        id=str(uuid4()),
        parent_id="test-user-id",
        grade_level=4,
        display_name="S",
        is_active=True,
    )
    # Standard FK for PlanModule.standard_id and GeneratedQuestion.standard_id
    standard = Standard(
        id="4.NBT.A.1",
        standard_code="4.NBT.A.1",
        grade_level=4,
        domain="NBT",
        title="Place value",
        description="Recognize that a multi-digit whole number is composed of place values.",
    )
    plan = LearningPlan(
        id=str(uuid4()),
        student_id=student.id,
        track="on_track",
        status="active",
        total_modules=1,
        total_lessons=1,
        estimated_total_minutes=30,
        estimated_completion_date=date(2026, 12, 31),
    )
    module = PlanModule(
        id=str(uuid4()),
        plan_id=plan.id,
        standard_id="4.NBT.A.1",
        sequence_order=1,
        lesson_count=1,
        estimated_minutes=30,
    )
    lesson = PlanLesson(
        id=str(uuid4()),
        module_id=module.id,
        sequence_order=1,
        title="Practice: Place Value",
    )
    session = PracticeSession(
        id=str(uuid4()),
        lesson_id=lesson.id,
        student_id=student.id,
        standard_code="4.NBT.A.1",
        question_count=2,
    )
    # GeneratedQuestion requires a job_id FK to generation_jobs
    gen_job = GenerationJob(
        id=str(uuid4()),
        standard_id="4.NBT.A.1",
        requested_count=2,
        status="completed",
        model="o3-mini",
    )
    q1 = GeneratedQuestion(
        id=str(uuid4()),
        job_id=gen_job.id,
        standard_id="4.NBT.A.1",
        correct_answer="4",
        difficulty=1,
        stem="2+2?",
        options=["2", "3", "4", "5"],
        model_used="o3-mini",
        validation_status="passed",
    )
    q2 = GeneratedQuestion(
        id=str(uuid4()),
        job_id=gen_job.id,
        standard_id="4.NBT.A.1",
        correct_answer="6",
        difficulty=1,
        stem="3+3?",
        options=["4", "5", "6", "7"],
        model_used="o3-mini",
        validation_status="passed",
    )
    psq1 = PracticeSessionQuestion(
        id=str(uuid4()),
        session_id=session.id,
        question_id=q1.id,
        sequence=0,
        difficulty=1,
    )
    psq2 = PracticeSessionQuestion(
        id=str(uuid4()),
        session_id=session.id,
        question_id=q2.id,
        sequence=1,
        difficulty=1,
    )
    # Insert in dependency order with explicit flushes
    async_db_session.add_all([parent, student, standard])
    await async_db_session.flush()

    async_db_session.add_all([plan, gen_job])
    await async_db_session.flush()

    async_db_session.add(module)
    await async_db_session.flush()

    async_db_session.add(lesson)
    await async_db_session.flush()

    async_db_session.add(session)
    await async_db_session.flush()

    async_db_session.add_all([q1, q2])
    await async_db_session.flush()

    async_db_session.add_all([psq1, psq2])
    await async_db_session.flush()

    return {"session": session, "psq1": psq1, "psq2": psq2, "q1": q1, "q2": q2}


@pytest.mark.asyncio
async def test_submit_correct_answer_updates_row_and_returns_progress(
    client, session_flow_seed, async_db_session
):
    session = session_flow_seed["session"]

    response = await client.post(
        f"/api/v1/sessions/{session.id}/answer",
        json={"answer": "4", "time_spent_ms": 1500},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["correct"] is True
    assert data["correct_answer"] == "4"
    assert data["progress"]["current_question"] == 1
    assert data["progress"]["total_questions"] == 2

    # Verify the PracticeSessionQuestion row was updated in place
    await async_db_session.refresh(session_flow_seed["psq1"])
    assert session_flow_seed["psq1"].student_answer == "4"
    assert session_flow_seed["psq1"].is_correct is True
    assert session_flow_seed["psq1"].time_spent_ms == 1500
    assert session_flow_seed["psq1"].answered_at is not None


@pytest.mark.asyncio
async def test_submit_answer_advances_to_next_unanswered_question(
    client, session_flow_seed, async_db_session
):
    session = session_flow_seed["session"]

    # First answer — sequence 0
    r1 = await client.post(
        f"/api/v1/sessions/{session.id}/answer",
        json={"answer": "4", "time_spent_ms": 1000},
    )
    assert r1.status_code == 200
    assert r1.json()["progress"]["current_question"] == 1

    # Second answer — sequence 1
    r2 = await client.post(
        f"/api/v1/sessions/{session.id}/answer",
        json={"answer": "6", "time_spent_ms": 1200},
    )
    assert r2.status_code == 200
    assert r2.json()["correct"] is True
    assert r2.json()["progress"]["current_question"] == 2

    # Third attempt — no unanswered remaining → 409
    r3 = await client.post(
        f"/api/v1/sessions/{session.id}/answer",
        json={"answer": "anything", "time_spent_ms": 100},
    )
    assert r3.status_code == 409, r3.text


@pytest.mark.asyncio
async def test_submit_incorrect_answer_records_is_correct_false(
    client, session_flow_seed, async_db_session
):
    session = session_flow_seed["session"]
    response = await client.post(
        f"/api/v1/sessions/{session.id}/answer",
        json={"answer": "wrong", "time_spent_ms": 500},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] is False
    assert data["correct_answer"] == "4"
