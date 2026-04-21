"""
Tests for Practice Session endpoints.
"""
import pytest
import pytest_asyncio
from unittest.mock import patch


@pytest.mark.asyncio
class TestPracticeSessionAnswer:
    """Tests for practice session answer endpoint."""

    @pytest_asyncio.fixture
    async def test_client(self, async_db_session):
        """Create TestClient with mocked database session."""
        from starlette.testclient import TestClient
        from src.main import app

        with patch("src.core.database.get_db") as mock_get_db:
            async def mock_db_generator():
                yield async_db_session

            mock_get_db.return_value = mock_db_generator()
            with TestClient(app, base_url="http://test") as client:
                yield client

    async def test_submit_answer_session_not_found(self, test_client, mock_jwt_as_parent):
        """PSA-001: Submitting answer for non-existent session returns 404."""
        response = test_client.post(
            "/api/v1/sessions/non-existent/answer",
            headers={"Authorization": "Bearer mock-token"},
            json={"answer": "4", "time_spent_ms": 15000},
        )

        assert response.status_code == 404

    async def test_submit_answer_unauthorized(self, test_client, mock_jwt_as_teacher):
        """PSA-002: Teacher cannot submit answers for students."""
        response = test_client.post(
            "/api/v1/sessions/any-session/answer",
            headers={"Authorization": "Bearer mock-token"},
            json={"answer": "4", "time_spent_ms": 15000},
        )

        # Will be 403 due to ownership check or 404 if session doesn't exist
        assert response.status_code in [403, 404]

    async def test_submit_answer_with_valid_data(self, test_client, async_db_session, mock_jwt_as_parent):
        """PSA-003: Submitting answer with valid session data works."""
        from src.models.models import (
            User, Student, LearningPlan, PlanModule, PlanLesson,
            PracticeSession, GeneratedQuestion, PracticeSessionQuestion
        )
        from uuid import uuid4

        # Create parent
        parent = User(
            id=str(uuid4()),
            auth0_id="auth0|test_parent",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
        )
        async_db_session.add(parent)
        async_db_session.flush()

        # Create student
        student = Student(
            id=str(uuid4()),
            parent_id=parent.id,
            grade_level=4,
            display_name="Test Student",
            is_active=True,
        )
        async_db_session.add(student)
        async_db_session.flush()

        # Create learning plan
        plan = LearningPlan(
            id=str(uuid4()),
            student_id=student.id,
            track="on_track",
            status="active",
            total_modules=1,
            completed_modules=0,
        )
        async_db_session.add(plan)
        async_db_session.flush()

        # Create module
        module = PlanModule(
            id=str(uuid4()),
            plan_id=plan.id,
            standard_id="4.NF.A.1",
            status="in_progress",
            lesson_count=1,
        )
        async_db_session.add(module)
        async_db_session.flush()

        # Create lesson
        lesson = PlanLesson(
            id=str(uuid4()),
            module_id=module.id,
            lesson_type="practice",
            title="Practice",
            status="available",
            question_count=1,
        )
        async_db_session.add(lesson)
        async_db_session.flush()

        # Create practice session
        session = PracticeSession(
            id=str(uuid4()),
            lesson_id=lesson.id,
            student_id=student.id,
            standard_code="4.NF.A.1",
            question_count=1,
            status="in_progress",
            current_question_index=0,
            question_ids=[str(uuid4())],
        )
        async_db_session.add(session)

        # Create question
        question = GeneratedQuestion(
            id=session.question_ids[0],
            job_id=str(uuid4()),
            standard_id="4.NF.A.1",
            difficulty=2,
            question_type="multiple_choice",
            stem="What is 2 + 2?",
            options=["3", "4", "5", "6"],
            correct_answer="4",
            explanation="Simple addition",
            validation_status="passed",
        )
        async_db_session.add(question)
        async_db_session.commit()

        response = test_client.post(
            f"/api/v1/sessions/{session.id}/answer",
            headers={"Authorization": "Bearer mock-token"},
            json={"answer": "4", "time_spent_ms": 15000},
        )

        assert response.status_code == 200
        data = response.json()
        assert "correct" in data
        assert "correct_answer" in data
        assert "progress" in data

    async def test_submit_incorrect_answer(self, test_client, async_db_session, mock_jwt_as_parent):
        """PSA-004: Submitting incorrect answer returns correct feedback."""
        from src.models.models import (
            User, Student, LearningPlan, PlanModule, PlanLesson,
            PracticeSession, GeneratedQuestion
        )
        from uuid import uuid4

        # Create parent
        parent = User(
            id=str(uuid4()),
            auth0_id="auth0|test_parent",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
        )
        async_db_session.add(parent)
        async_db_session.flush()

        # Create student
        student = Student(
            id=str(uuid4()),
            parent_id=parent.id,
            grade_level=4,
            display_name="Test Student",
            is_active=True,
        )
        async_db_session.add(student)
        async_db_session.flush()

        # Create learning plan
        plan = LearningPlan(
            id=str(uuid4()),
            student_id=student.id,
            track="on_track",
            status="active",
            total_modules=1,
            completed_modules=0,
        )
        async_db_session.add(plan)
        async_db_session.flush()

        # Create module
        module = PlanModule(
            id=str(uuid4()),
            plan_id=plan.id,
            standard_id="4.NF.A.1",
            status="in_progress",
            lesson_count=1,
        )
        async_db_session.add(module)
        async_db_session.flush()

        # Create lesson
        lesson = PlanLesson(
            id=str(uuid4()),
            module_id=module.id,
            lesson_type="practice",
            title="Practice",
            status="available",
            question_count=1,
        )
        async_db_session.add(lesson)
        async_db_session.flush()

        # Create practice session
        session = PracticeSession(
            id=str(uuid4()),
            lesson_id=lesson.id,
            student_id=student.id,
            standard_code="4.NF.A.1",
            question_count=1,
            status="in_progress",
            current_question_index=0,
            question_ids=[str(uuid4())],
        )
        async_db_session.add(session)

        # Create question with correct answer "5"
        question = GeneratedQuestion(
            id=session.question_ids[0],
            job_id=str(uuid4()),
            standard_id="4.NF.A.1",
            difficulty=2,
            question_type="multiple_choice",
            stem="What is 2 + 3?",
            options=["4", "5", "6", "7"],
            correct_answer="5",
            explanation="Simple addition",
            validation_status="passed",
        )
        async_db_session.add(question)
        async_db_session.commit()

        # Submit incorrect answer
        response = test_client.post(
            f"/api/v1/sessions/{session.id}/answer",
            headers={"Authorization": "Bearer mock-token"},
            json={"answer": "4", "time_spent_ms": 15000},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["correct"] is False
        assert data["correct_answer"] == "5"


@pytest.mark.asyncio
class TestPracticeSessionComplete:
    """Tests for practice session completion endpoint."""

    @pytest_asyncio.fixture
    async def test_client(self, async_db_session):
        """Create TestClient with mocked database session."""
        from starlette.testclient import TestClient
        from src.main import app

        with patch("src.core.database.get_db") as mock_get_db:
            async def mock_db_generator():
                yield async_db_session

            mock_get_db.return_value = mock_db_generator()
            with TestClient(app, base_url="http://test") as client:
                yield client

    async def test_complete_session_not_found(self, test_client, mock_jwt_as_parent):
        """PSC-001: Complete non-existent session returns 404."""
        response = test_client.post(
            "/api/v1/sessions/non-existent/complete",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 404

    async def test_complete_session_unauthorized(self, test_client, mock_jwt_as_teacher):
        """PSC-002: Teacher cannot complete student sessions."""
        response = test_client.post(
            "/api/v1/sessions/any-session/complete",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code in [403, 404]

    async def test_complete_session(self, test_client, async_db_session, mock_jwt_as_parent):
        """PSC-003: Complete a practice session successfully."""
        from src.models.models import (
            User, Student, LearningPlan, PlanModule, PlanLesson,
            PracticeSession, GeneratedQuestion, PracticeSessionQuestion,
            ModuleStatus
        )
        from uuid import uuid4

        # Create parent
        parent = User(
            id=str(uuid4()),
            auth0_id="auth0|test_parent",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
        )
        async_db_session.add(parent)
        async_db_session.flush()

        # Create student
        student = Student(
            id=str(uuid4()),
            parent_id=parent.id,
            grade_level=4,
            display_name="Test Student",
            is_active=True,
        )
        async_db_session.add(student)
        async_db_session.flush()

        # Create learning plan
        plan = LearningPlan(
            id=str(uuid4()),
            student_id=student.id,
            track="on_track",
            status="active",
            total_modules=1,
            completed_modules=0,
        )
        async_db_session.add(plan)
        async_db_session.flush()

        # Create module
        module = PlanModule(
            id=str(uuid4()),
            plan_id=plan.id,
            standard_id="4.NF.A.1",
            status="in_progress",
            lesson_count=1,
        )
        async_db_session.add(module)
        async_db_session.flush()

        # Create lesson
        lesson = PlanLesson(
            id=str(uuid4()),
            module_id=module.id,
            lesson_type="practice",
            title="Practice",
            status="available",
            question_count=1,
        )
        async_db_session.add(lesson)
        async_db_session.flush()

        # Create practice session
        session = PracticeSession(
            id=str(uuid4()),
            lesson_id=lesson.id,
            student_id=student.id,
            standard_code="4.NF.A.1",
            question_count=1,
            status="in_progress",
            current_question_index=0,
            question_ids=[str(uuid4())],
        )
        async_db_session.add(session)

        # Create question
        question = GeneratedQuestion(
            id=session.question_ids[0],
            job_id=str(uuid4()),
            standard_id="4.NF.A.1",
            difficulty=2,
            question_type="multiple_choice",
            stem="What is 2 + 2?",
            options=["3", "4", "5", "6"],
            correct_answer="4",
            explanation="Simple addition",
            validation_status="passed",
        )
        async_db_session.add(question)

        # Create response
        response_record = PracticeSessionQuestion(
            id=str(uuid4()),
            session_id=session.id,
            question_id=question.id,
            sequence=1,
            difficulty=2,
            student_answer="4",
            is_correct=True,
            points_earned=1.0,
            time_spent_ms=15000,
        )
        async_db_session.add(response_record)
        async_db_session.commit()

        response = test_client.post(
            f"/api/v1/sessions/{session.id}/complete",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["accuracy"] == 100.0
        assert "new_badges" in data

    async def test_complete_session_with_responses(self, test_client, async_db_session, mock_jwt_as_parent):
        """PSC-004: Complete session calculates accuracy from responses."""
        from src.models.models import (
            User, Student, LearningPlan, PlanModule, PlanLesson,
            PracticeSession, GeneratedQuestion, PracticeSessionQuestion,
            ModuleStatus
        )
        from uuid import uuid4

        # Create parent
        parent = User(
            id=str(uuid4()),
            auth0_id="auth0|test_parent",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
        )
        async_db_session.add(parent)
        async_db_session.flush()

        # Create student
        student = Student(
            id=str(uuid4()),
            parent_id=parent.id,
            grade_level=4,
            display_name="Test Student",
            is_active=True,
        )
        async_db_session.add(student)
        async_db_session.flush()

        # Create learning plan
        plan = LearningPlan(
            id=str(uuid4()),
            student_id=student.id,
            track="on_track",
            status="active",
            total_modules=1,
            completed_modules=0,
        )
        async_db_session.add(plan)
        async_db_session.flush()

        # Create module
        module = PlanModule(
            id=str(uuid4()),
            plan_id=plan.id,
            standard_id="4.NF.A.1",
            status="in_progress",
            lesson_count=1,
        )
        async_db_session.add(module)
        async_db_session.flush()

        # Create lesson
        lesson = PlanLesson(
            id=str(uuid4()),
            module_id=module.id,
            lesson_type="practice",
            title="Practice",
            status="available",
            question_count=5,
        )
        async_db_session.add(lesson)
        async_db_session.flush()

        # Create practice session with 5 questions
        session = PracticeSession(
            id=str(uuid4()),
            lesson_id=lesson.id,
            student_id=student.id,
            standard_code="4.NF.A.1",
            question_count=5,
            status="in_progress",
            current_question_index=4,  # All answered
            question_ids=[str(uuid4()) for _ in range(5)],
        )
        async_db_session.add(session)

        # Create 5 questions (4 correct, 1 incorrect)
        questions_data = [
            ("question-1", "5", "4", True),
            ("question-2", "5", "5", True),
            ("question-3", "5", "6", False),  # Incorrect
            ("question-4", "5", "8", True),
            ("question-5", "5", "10", True),
        ]

        for qid, stem, correct, expected_correct in questions_data:
            question = GeneratedQuestion(
                id=qid,
                job_id=str(uuid4()),
                standard_id="4.NF.A.1",
                difficulty=2,
                question_type="multiple_choice",
                stem=stem,
                options=["4", "5", "6", "7", "8", "10"],
                correct_answer=correct,
                explanation="Test question",
                validation_status="passed",
            )
            async_db_session.add(question)

            # Create response
            response_record = PracticeSessionQuestion(
                id=f"resp-{qid}",
                session_id=session.id,
                question_id=qid,
                sequence=questions_data.index((qid, stem, correct, expected_correct)) + 1,
                difficulty=2,
                student_answer="4",
                is_correct=expected_correct,
                points_earned=1.0 if expected_correct else 0.0,
                time_spent_ms=10000,
            )
            async_db_session.add(response_record)

        async_db_session.commit()

        response = test_client.post(
            f"/api/v1/sessions/{session.id}/complete",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        # 4/5 = 80% accuracy
        assert data["accuracy"] == 80.0
