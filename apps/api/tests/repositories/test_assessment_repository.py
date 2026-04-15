"""Tests for assessment repository."""

import pytest
from datetime import datetime


class TestAssessmentRepository:
    """Test AssessmentRepository."""

    @pytest.fixture
    def repository(self, session):
        """Create AssessmentRepository for tests."""
        from src.repositories.assessment_repository import AssessmentRepository
        from src.models.models import Assessment

        return AssessmentRepository(session)

    def test_create_session(self, repository, student):
        """create_session creates assessment session."""
        from src.models.models import Assessment

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        repository.session.add(assessment)
        repository.session.commit()

        session_result = repository.create_session(
            assessment_id=assessment.id,
            student_id=student.id,
        )

        assert session_result.assessment_id == assessment.id
        assert session_result.student_id == student.id
        assert session_result.status == "in_progress"
        assert session_result.started_at is not None

    def test_get_session(self, repository, student):
        """get_session retrieves session by ID."""
        from src.models.models import Assessment, AssessmentSession

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        repository.session.add(assessment)
        repository.session.commit()

        session = AssessmentSession(
            id="session-1",
            assessment_id=assessment.id,
            student_id=student.id,
            status="in_progress",
        )
        repository.session.add(session)
        repository.session.commit()

        result = repository.get_session("session-1")

        assert result is not None
        assert result.id == "session-1"

    def test_get_session_not_found(self, repository, student):
        """get_session returns None for missing session."""
        result = repository.get_session("missing-session")
        assert result is None

    def test_complete_session(self, repository, student):
        """complete_session marks session as completed."""
        from src.models.models import Assessment, AssessmentSession

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        repository.session.add(assessment)
        repository.session.commit()

        session = AssessmentSession(
            id="session-1",
            assessment_id=assessment.id,
            student_id=student.id,
            status="in_progress",
        )
        repository.session.add(session)
        repository.session.commit()

        completed_at = datetime.utcnow()
        result = repository.complete_session("session-1", completed_at)

        assert result is not None
        assert result.status == "completed"
        assert result.completed_at == completed_at

    def test_record_response(self, repository, student):
        """record_response records student response."""
        from src.models.models import Assessment, AssessmentSession, Question

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        repository.session.add(assessment)
        repository.session.commit()

        session = AssessmentSession(
            id="session-1",
            assessment_id=assessment.id,
            student_id=student.id,
            status="in_progress",
        )
        repository.session.add(session)
        repository.session.commit()

        question = Question(
            id="q1",
            standard_id="4.NBT.A.1",
            question_text="Test?",
            question_type="multiple_choice",
            difficulty=3,
        )
        repository.session.add(question)
        repository.session.commit()

        response = repository.record_response(
            session_id=session.id,
            question_id=question.id,
            student_answer="A",
            is_correct=True,
            points_earned=1.0,
            time_spent_seconds=60,
        )

        assert response.question_id == question.id
        assert response.student_answer == "A"
        assert response.is_correct is True
        assert response.points_earned == 1.0
        assert response.time_spent_seconds == 60

    def test_get_responses_for_session(self, repository, student):
        """get_responses_for_session retrieves all responses."""
        from src.models.models import Assessment, AssessmentSession, Question

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        repository.session.add(assessment)
        repository.session.commit()

        session = AssessmentSession(
            id="session-1",
            assessment_id=assessment.id,
            student_id=student.id,
            status="in_progress",
        )
        repository.session.add(session)
        repository.session.commit()

        question1 = Question(
            id="q1",
            standard_id="4.NBT.A.1",
            question_text="Test 1?",
            question_type="multiple_choice",
            difficulty=3,
        )
        question2 = Question(
            id="q2",
            standard_id="4.NBT.A.2",
            question_text="Test 2?",
            question_type="multiple_choice",
            difficulty=4,
        )
        repository.session.add(question1)
        repository.session.add(question2)
        repository.session.commit()

        response1 = repository.record_response(
            session_id=session.id,
            question_id=question1.id,
            student_answer="A",
            is_correct=True,
            points_earned=1.0,
            time_spent_seconds=60,
        )

        response2 = repository.record_response(
            session_id=session.id,
            question_id=question2.id,
            student_answer="B",
            is_correct=False,
            points_earned=0.0,
            time_spent_seconds=90,
        )

        responses = repository.get_responses_for_session(session.id)

        assert len(responses) == 2
        response_ids = {r.id for r in responses}
        assert response1.id in response_ids
        assert response2.id in response_ids

    def test_get_active_diagnostic(self, repository, student):
        """get_active_diagnostic returns in-progress diagnostic."""
        from src.models.models import Assessment

        # Create completed assessment
        completed = Assessment(
            id="assess-completed",
            student_id=student.id,
            assessment_type="diagnostic",
            status="completed",
        )
        repository.session.add(completed)

        # Create in-progress assessment
        in_progress = Assessment(
            id="assess-active",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        repository.session.add(in_progress)
        repository.session.commit()

        result = repository.get_active_diagnostic(student.id)

        assert result is not None
        assert result.id == "assess-active"
        assert result.status == "in_progress"

    def test_get_active_diagnostic_none(self, repository, student):
        """get_active_diagnostic returns None when no active assessment."""
        from src.models.models import Assessment

        # Create only completed assessments
        completed = Assessment(
            id="assess-completed",
            student_id=student.id,
            assessment_type="diagnostic",
            status="completed",
        )
        repository.session.add(completed)
        repository.session.commit()

        result = repository.get_active_diagnostic(student.id)

        assert result is None

    def test_update_assessment_status(self, repository, student):
        """update_assessment_status changes assessment status."""
        from src.models.models import Assessment

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        repository.session.add(assessment)
        repository.session.commit()

        result = repository.update_assessment_status(
            assessment_id="assess-1",
            status="completed",
            total_score=0.85,
        )

        assert result is not None
        assert result.status == "completed"
        assert result.total_score == 0.85

    def test_update_assessment_status_not_found(self, repository, student):
        """update_assessment_status returns None for missing assessment."""
        result = repository.update_assessment_status(
            assessment_id="missing-assessment",
            status="completed",
            total_score=0.85,
        )

        assert result is None


class TestAssessmentSessionRepository:
    """Test AssessmentSessionRepository."""

    @pytest.fixture
    def repository(self, session, student):
        """Create AssessmentSessionRepository for tests."""
        from src.repositories.assessment_repository import AssessmentSessionRepository

        return AssessmentSessionRepository(session)

    def test_get_active_for_student(self, repository, student):
        """get_active_for_student checks if student has active assessment."""
        from src.models.models import Assessment, AssessmentSession

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="in_progress",
        )
        session = AssessmentSession(
            id="session-1",
            assessment_id=assessment.id,
            student_id=student.id,
            status="in_progress",
        )
        repository.session.add(assessment)
        repository.session.add(session)
        repository.session.commit()

        result = repository.get_active_for_student(student.id)

        assert result is True

    def test_get_active_for_student_completed(self, repository, student):
        """get_active_for_student returns False for completed assessment."""
        from src.models.models import Assessment, AssessmentSession

        assessment = Assessment(
            id="assess-1",
            student_id=student.id,
            assessment_type="diagnostic",
            status="completed",
        )
        session = AssessmentSession(
            id="session-1",
            assessment_id=assessment.id,
            student_id=student.id,
            status="completed",
        )
        repository.session.add(assessment)
        repository.session.add(session)
        repository.session.commit()

        result = repository.get_active_for_student(student.id)

        assert result is False

    def test_get_active_for_student_none(self, repository, student):
        """get_active_for_student returns False when no sessions."""
        result = repository.get_active_for_student(student.id)
        assert result is False
