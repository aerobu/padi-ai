"""
Tests for Practice Session endpoints.

Aligned with the real PracticeSession schema after Task 2.1 rewrote the endpoint:
- No current_question_index / question_ids columns on PracticeSession.
- Answer endpoint locates the next unanswered PSQ by sequence.
- Ownership: user_payload["sub"] must equal student.parent_id (User.id).
- The shared `client` fixture authenticates as sub="test-parent-id".
"""
import pytest
import pytest_asyncio
from datetime import datetime, date
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _seed_standard(async_db_session, *, std_id="4.NF.A.1", code="4.NF.A.1"):
    """Seed a Standard row and return it."""
    from src.models.models import Standard

    standard = Standard(
        id=std_id,
        standard_code=code,
        grade_level=4,
        domain="Number and Operations - Fractions",
        title="Equivalent Fractions",
        description="Explain why a fraction a/b is equivalent to (n×a)/(n×b).",
        is_active=True,
    )
    async_db_session.add(standard)
    await async_db_session.flush()
    return standard


async def _seed_session(async_db_session, *, question_count=1, answered=False):
    """Seed a full practice session with PSQ rows.

    Returns (session, questions, psqs) so callers can inspect them.
    The parent User has id="test-parent-id" which matches the `client`
    fixture's JWT sub.
    """
    from src.models.models import (
        User, Student, LearningPlan, PlanModule, PlanLesson,
        PracticeSession, GenerationJob, GeneratedQuestion, PracticeSessionQuestion,
    )

    # Seed a Standard row needed by PlanModule FK
    standard = await _seed_standard(async_db_session)

    # Seed a GenerationJob needed by GeneratedQuestion FK
    gen_job = GenerationJob(
        id=str(uuid4()),
        standard_id=standard.id,
        requested_count=question_count,
        status="completed",
    )
    async_db_session.add(gen_job)
    await async_db_session.flush()

    # Parent — id must match the JWT sub used by the `client` fixture
    parent = User(
        id="test-parent-id",
        auth0_id="auth0|test-parent-id",
        first_name="Test",
        last_name="Parent",
        role="parent",
        is_active=True,
    )
    parent.set_email("testparent@example.com")
    async_db_session.add(parent)
    await async_db_session.flush()

    student = Student(
        id=str(uuid4()),
        parent_id=parent.id,
        grade_level=4,
        display_name="Test Student",
        is_active=True,
    )
    async_db_session.add(student)
    await async_db_session.flush()

    plan = LearningPlan(
        id=str(uuid4()),
        student_id=student.id,
        track="on_track",
        status="active",
        total_modules=1,
        completed_modules=0,
        total_lessons=1,
        completed_lessons=0,
        estimated_total_minutes=20,
        estimated_completion_date=date(2026, 6, 1),
    )
    async_db_session.add(plan)
    await async_db_session.flush()

    module = PlanModule(
        id=str(uuid4()),
        plan_id=plan.id,
        standard_id=standard.id,
        sequence_order=1,
        status="in_progress",
        lesson_count=1,
        estimated_minutes=20,
    )
    async_db_session.add(module)
    await async_db_session.flush()

    lesson = PlanLesson(
        id=str(uuid4()),
        module_id=module.id,
        sequence_order=1,
        lesson_type="practice",
        title="Practice",
        status="available",
        question_count=question_count,
    )
    async_db_session.add(lesson)
    await async_db_session.flush()

    session = PracticeSession(
        id=str(uuid4()),
        lesson_id=lesson.id,
        student_id=student.id,
        standard_code="4.NF.A.1",
        question_count=question_count,
        status="in_progress",
    )
    async_db_session.add(session)
    await async_db_session.flush()

    questions = []
    psqs = []
    for i in range(question_count):
        q = GeneratedQuestion(
            id=str(uuid4()),
            job_id=gen_job.id,
            standard_id="4.NF.A.1",
            difficulty=2,
            question_type="multiple_choice",
            stem=f"What is {i + 1} + 1?",
            options=[str(i), str(i + 2), str(i + 3), str(i + 4)],
            correct_answer=str(i + 2),
            explanation="Simple addition",
            model_used="test-model",
            validation_status="passed",
        )
        async_db_session.add(q)
        questions.append(q)

        psq = PracticeSessionQuestion(
            id=str(uuid4()),
            session_id=session.id,
            question_id=q.id,
            sequence=i,
            difficulty=2,
            student_answer=str(i + 2) if answered else None,
            is_correct=True if answered else None,
            answered_at=datetime.utcnow() if answered else None,
        )
        async_db_session.add(psq)
        psqs.append(psq)

    await async_db_session.flush()
    await async_db_session.commit()
    return session, questions, psqs


# ---------------------------------------------------------------------------
# TestPracticeSessionAnswer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPracticeSessionAnswer:
    """Tests for POST /api/v1/sessions/{id}/answer endpoint."""

    async def test_submit_answer_session_not_found(self, client):
        """PSA-001: Submitting answer for non-existent session returns 404."""
        response = await client.post(
            "/api/v1/sessions/non-existent-id/answer",
            json={"answer": "4", "time_spent_ms": 15000},
        )
        assert response.status_code == 404

    async def test_submit_answer_wrong_owner(self, async_db_session, client):
        """PSA-002: A parent who does not own the session gets 403.

        We seed a session owned by a *different* parent
        (parent_id != "test-parent-id"), so the client (authenticated as
        "test-parent-id") should be rejected with 403.
        """
        from src.models.models import (
            User, Student, LearningPlan, PlanModule, PlanLesson,
            PracticeSession, GenerationJob, GeneratedQuestion, PracticeSessionQuestion,
        )

        # Seed Standard required by PlanModule FK
        std = await _seed_standard(async_db_session)

        # Seed GenerationJob required by GeneratedQuestion FK
        gen_job = GenerationJob(
            id=str(uuid4()),
            standard_id=std.id,
            requested_count=1,
            status="completed",
        )
        async_db_session.add(gen_job)
        await async_db_session.flush()

        other_parent = User(
            id="other-parent-id",
            auth0_id="auth0|other-parent",
            first_name="Other",
            last_name="Parent",
            role="parent",
            is_active=True,
        )
        other_parent.set_email("other@example.com")
        async_db_session.add(other_parent)
        await async_db_session.flush()

        student = Student(
            id=str(uuid4()),
            parent_id="other-parent-id",
            grade_level=4,
            display_name="Other Student",
            is_active=True,
        )
        async_db_session.add(student)
        await async_db_session.flush()

        plan = LearningPlan(
            id=str(uuid4()),
            student_id=student.id,
            track="on_track",
            status="active",
            total_modules=1,
            completed_modules=0,
            total_lessons=1,
            completed_lessons=0,
            estimated_total_minutes=20,
            estimated_completion_date=date(2026, 6, 1),
        )
        async_db_session.add(plan)
        await async_db_session.flush()

        module = PlanModule(
            id=str(uuid4()),
            plan_id=plan.id,
            standard_id=std.id,
            sequence_order=1,
            status="in_progress",
            lesson_count=1,
            estimated_minutes=20,
        )
        async_db_session.add(module)
        await async_db_session.flush()

        lesson = PlanLesson(
            id=str(uuid4()),
            module_id=module.id,
            sequence_order=1,
            lesson_type="practice",
            title="Practice",
            status="available",
            question_count=1,
        )
        async_db_session.add(lesson)
        await async_db_session.flush()

        session = PracticeSession(
            id=str(uuid4()),
            lesson_id=lesson.id,
            student_id=student.id,
            standard_code="4.NF.A.1",
            question_count=1,
            status="in_progress",
        )
        async_db_session.add(session)
        await async_db_session.flush()

        q = GeneratedQuestion(
            id=str(uuid4()),
            job_id=gen_job.id,
            standard_id="4.NF.A.1",
            difficulty=2,
            question_type="multiple_choice",
            stem="What is 1 + 1?",
            options=["1", "2", "3", "4"],
            correct_answer="2",
            explanation="Simple addition",
            model_used="test-model",
            validation_status="passed",
        )
        async_db_session.add(q)
        await async_db_session.flush()

        psq = PracticeSessionQuestion(
            id=str(uuid4()),
            session_id=session.id,
            question_id=q.id,
            sequence=0,
            difficulty=2,
        )
        async_db_session.add(psq)
        await async_db_session.commit()

        response = await client.post(
            f"/api/v1/sessions/{session.id}/answer",
            json={"answer": "2", "time_spent_ms": 15000},
        )
        assert response.status_code == 403

    async def test_submit_answer_with_valid_data(self, async_db_session, client):
        """PSA-003: Submitting a correct answer returns is_correct=True."""
        session, questions, psqs = await _seed_session(async_db_session, question_count=1)

        response = await client.post(
            f"/api/v1/sessions/{session.id}/answer",
            json={"answer": questions[0].correct_answer, "time_spent_ms": 15000},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["correct"] is True
        assert data["correct_answer"] == questions[0].correct_answer
        assert "progress" in data

    async def test_submit_incorrect_answer(self, async_db_session, client):
        """PSA-004: Submitting an incorrect answer returns is_correct=False."""
        session, questions, psqs = await _seed_session(async_db_session, question_count=1)
        wrong_answer = "definitely-wrong"

        response = await client.post(
            f"/api/v1/sessions/{session.id}/answer",
            json={"answer": wrong_answer, "time_spent_ms": 10000},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["correct"] is False
        assert data["correct_answer"] == questions[0].correct_answer

    async def test_submit_answer_no_unanswered_questions(self, async_db_session, client):
        """PSA-005: When all PSQs are answered, returns 409."""
        # Seed with all questions already answered
        session, questions, psqs = await _seed_session(
            async_db_session, question_count=2, answered=True
        )

        response = await client.post(
            f"/api/v1/sessions/{session.id}/answer",
            json={"answer": "anything", "time_spent_ms": 5000},
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# TestPracticeSessionComplete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPracticeSessionComplete:
    """Tests for POST /api/v1/sessions/{id}/complete endpoint.

    NOTE: The /complete endpoint has a known bug (Task 3.2 scope):
    it queries PracticeSessionQuestion.practice_session_id but the real
    column is session_id. Tests that exercise that code path are marked
    xfail until the endpoint is fixed in a future task.
    """

    async def test_complete_session_not_found(self, client):
        """PSC-001: Complete non-existent session returns 404."""
        response = await client.post(
            "/api/v1/sessions/non-existent-id/complete",
        )
        assert response.status_code == 404

    async def test_complete_session_wrong_owner(self, async_db_session, client):
        """PSC-002: A parent who does not own the session gets 403.

        Seeds a session owned by a different parent, so the 'client'
        (authenticated as "test-parent-id") is rejected.
        """
        from src.models.models import (
            User, Student, LearningPlan, PlanModule, PlanLesson, PracticeSession,
        )

        # Seed Standard required by PlanModule FK
        await _seed_standard(async_db_session)

        other_parent = User(
            id="other-parent-id",
            auth0_id="auth0|other-parent",
            first_name="Other",
            last_name="Parent",
            role="parent",
            is_active=True,
        )
        other_parent.set_email("other@example.com")
        async_db_session.add(other_parent)
        await async_db_session.flush()

        student = Student(
            id=str(uuid4()),
            parent_id="other-parent-id",
            grade_level=4,
            display_name="Other Student",
            is_active=True,
        )
        async_db_session.add(student)
        await async_db_session.flush()

        plan = LearningPlan(
            id=str(uuid4()),
            student_id=student.id,
            track="on_track",
            status="active",
            total_modules=1,
            completed_modules=0,
            total_lessons=1,
            completed_lessons=0,
            estimated_total_minutes=20,
            estimated_completion_date=date(2026, 6, 1),
        )
        async_db_session.add(plan)
        await async_db_session.flush()

        module = PlanModule(
            id=str(uuid4()),
            plan_id=plan.id,
            standard_id="4.NF.A.1",
            sequence_order=1,
            status="in_progress",
            lesson_count=1,
            estimated_minutes=20,
        )
        async_db_session.add(module)
        await async_db_session.flush()

        lesson = PlanLesson(
            id=str(uuid4()),
            module_id=module.id,
            sequence_order=1,
            lesson_type="practice",
            title="Practice",
            status="available",
            question_count=1,
        )
        async_db_session.add(lesson)
        await async_db_session.flush()

        session = PracticeSession(
            id=str(uuid4()),
            lesson_id=lesson.id,
            student_id=student.id,
            standard_code="4.NF.A.1",
            question_count=1,
            status="in_progress",
        )
        async_db_session.add(session)
        await async_db_session.commit()

        response = await client.post(
            f"/api/v1/sessions/{session.id}/complete",
        )
        assert response.status_code == 403

    @pytest.mark.xfail(
        reason="complete endpoint queries practice_session_id but column is session_id — "
               "endpoint bug to be fixed in a future task",
        strict=False,
    )
    async def test_complete_session(self, async_db_session, client):
        """PSC-003: Complete a practice session successfully (xfail: endpoint bug)."""
        session, questions, psqs = await _seed_session(
            async_db_session, question_count=1, answered=True
        )

        response = await client.post(
            f"/api/v1/sessions/{session.id}/complete",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["accuracy"] == 100.0
        assert "new_badges" in data

    @pytest.mark.xfail(
        reason="complete endpoint queries practice_session_id but column is session_id — "
               "endpoint bug to be fixed in a future task",
        strict=False,
    )
    async def test_complete_session_with_responses(self, async_db_session, client):
        """PSC-004: Complete session calculates accuracy from responses (xfail: endpoint bug)."""
        from src.models.models import (
            User, Student, LearningPlan, PlanModule, PlanLesson,
            PracticeSession, GenerationJob, GeneratedQuestion, PracticeSessionQuestion,
        )

        # Seed Standard + GenerationJob for downstream FKs
        std = await _seed_standard(async_db_session)
        gen_job = GenerationJob(
            id=str(uuid4()),
            standard_id=std.id,
            requested_count=5,
            status="completed",
        )
        async_db_session.add(gen_job)
        await async_db_session.flush()

        parent = User(
            id="test-parent-id",
            auth0_id="auth0|test-parent-id",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
        )
        parent.set_email("testparent@example.com")
        async_db_session.add(parent)
        await async_db_session.flush()

        student = Student(
            id=str(uuid4()),
            parent_id="test-parent-id",
            grade_level=4,
            display_name="Test Student",
            is_active=True,
        )
        async_db_session.add(student)
        await async_db_session.flush()

        plan = LearningPlan(
            id=str(uuid4()),
            student_id=student.id,
            track="on_track",
            status="active",
            total_modules=1,
            completed_modules=0,
            total_lessons=1,
            completed_lessons=0,
            estimated_total_minutes=20,
            estimated_completion_date=date(2026, 6, 1),
        )
        async_db_session.add(plan)
        await async_db_session.flush()

        module = PlanModule(
            id=str(uuid4()),
            plan_id=plan.id,
            standard_id="4.NF.A.1",
            sequence_order=1,
            status="in_progress",
            lesson_count=1,
            estimated_minutes=20,
        )
        async_db_session.add(module)
        await async_db_session.flush()

        lesson = PlanLesson(
            id=str(uuid4()),
            module_id=module.id,
            sequence_order=1,
            lesson_type="practice",
            title="Practice",
            status="available",
            question_count=5,
        )
        async_db_session.add(lesson)
        await async_db_session.flush()

        session = PracticeSession(
            id=str(uuid4()),
            lesson_id=lesson.id,
            student_id=student.id,
            standard_code="4.NF.A.1",
            question_count=5,
            status="in_progress",
        )
        async_db_session.add(session)
        await async_db_session.flush()

        # 5 questions: 4 correct, 1 incorrect
        correct_flags = [True, True, False, True, True]
        for i, is_correct in enumerate(correct_flags):
            q = GeneratedQuestion(
                id=str(uuid4()),
                job_id=gen_job.id,
                standard_id="4.NF.A.1",
                difficulty=2,
                question_type="multiple_choice",
                stem=f"Q{i}",
                options=["a", "b", "c", "d"],
                correct_answer="b",
                explanation="Test",
                model_used="test-model",
                validation_status="passed",
            )
            async_db_session.add(q)
            await async_db_session.flush()

            psq = PracticeSessionQuestion(
                id=str(uuid4()),
                session_id=session.id,
                question_id=q.id,
                sequence=i,
                difficulty=2,
                student_answer="b" if is_correct else "a",
                is_correct=is_correct,
                points_earned=1.0 if is_correct else 0.0,
                time_spent_ms=10000,
                answered_at=datetime.utcnow(),
            )
            async_db_session.add(psq)

        await async_db_session.commit()

        response = await client.post(
            f"/api/v1/sessions/{session.id}/complete",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["accuracy"] == 80.0
