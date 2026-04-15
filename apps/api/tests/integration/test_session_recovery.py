"""Integration tests for session recovery and pause/resume.

This test suite validates that assessment sessions can be:
- Paused and resumed
- State persisted across browser sessions
- Recovered after network failures
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta


class TestSessionPause:
    """Test assessment session pause functionality."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def assessment_service(self, mock_db_session):
        """Create assessment service."""
        from src.services.assessment_service import AssessmentService
        from src.repositories.assessment_repository import AssessmentRepository
        from src.repositories.session_repository import AssessmentSessionRepository
        from src.repositories.student_repository import StudentRepository
        from src.repositories.standard_repository import StandardRepository
        from src.repositories.question_repository import QuestionRepository
        from src.repositories.consent_repository import ConsentRepository
        from src.services.bkt_service import BKTServiceservice
        from src.services.cat_service import CATService
        from src.core.redis_client import get_redis_client

        # Create mock repositories
        assessment_repo = AssessmentRepository(mock_db_session)
        session_repo = AssessmentSessionRepository(mock_db_session)
        student_repo = StudentRepository(mock_db_session)
        standard_repo = StandardRepository(mock_db_session)
        question_repo = QuestionRepository(mock_db_session)
        consent_repo = ConsentRepository(mock_db_session)
        bkt_service = BKTServiceservice()
        cat_service = CATService()
        redis_client = get_redis_client()

        return AssessmentService(
            assessment_repository=assessment_repo,
            session_repository=session_repo,
            student_repository=student_repo,
            standard_repository=standard_repo,
            question_repository=question_repo,
            consent_repository=consent_repo,
            bkt_service=bkt_service,
            cat_service=cat_service,
            redis_client=redis_client,
        )

    @pytest.mark.asyncio
    async def test_pause_session_success(self, assessment_service):
        """Session pause saves state to Redis."""
        # Mock existing session
        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_session.status = "active"

        assessment_service.session_repository.get_session = MagicMock()
        assessment_service.session_repository.get_session.return_value = mock_session

        # Mock Redis save
        assessment_service.redis_client.save_session_state = MagicMock()

        result = await assessment_service.pause_session(
            session_id="session-123",
            student_id="student-123",
        )

        assert result["success"] is True
        assessment_service.redis_client.save_session_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_session_no_active_session(self, assessment_service):
        """Pause session fails when no active session exists."""
        assessment_service.session_repository.get_session = MagicMock()
        assessment_service.session_repository.get_session.return_value = None

        with pytest.raises(ValueError, match="No active session found"):
            await assessment_service.pause_session(
                session_id="session-123",
                student_id="student-123",
            )


class TestSessionResume:
    """Test assessment session resume functionality."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def assessment_service(self, mock_db_session):
        """Create assessment service."""
        from src.services.assessment_service import AssessmentService
        from src.repositories.assessment_repository import AssessmentRepository
        from src.repositories.session_repository import AssessmentSessionRepository
        from src.repositories.student_repository import StudentRepository
        from src.repositories.standard_repository import StandardRepository
        from src.repositories.question_repository import QuestionRepository
        from src.repositories.consent_repository import ConsentRepository
        from src.services.bkt_service import BKTServiceservice
        from src.services.cat_service import CATService
        from src.core.redis_client import get_redis_client

        assessment_repo = AssessmentRepository(mock_db_session)
        session_repo = AssessmentSessionRepository(mock_db_session)
        student_repo = StudentRepository(mock_db_session)
        standard_repo = StandardRepository(mock_db_session)
        question_repo = QuestionRepository(mock_db_session)
        consent_repo = ConsentRepository(mock_db_session)
        bkt_service = BKTServiceservice()
        cat_service = CATService()
        redis_client = get_redis_client()

        return AssessmentService(
            assessment_repository=assessment_repo,
            session_repository=session_repo,
            student_repository=student_repo,
            standard_repository=standard_repo,
            question_repository=question_repo,
            consent_repository=consent_repo,
            bkt_service=bkt_service,
            cat_service=cat_service,
            redis_client=redis_client,
        )

    @pytest.mark.asyncio
    async def test_resume_session_success(self, assessment_service):
        """Session resume restores state from Redis."""
        # Mock Redis state
        mock_redis_state = {
            "assessment_id": "assessment-123",
            "session_id": "session-123",
            "current_question_id": "question-456",
            "questions_answered": 10,
            "answers": [],
            "bkt_states": {},
            "cat_state": {"theta": 0.5},
            "started_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
        }

        assessment_service.redis_client.get_session_state = MagicMock()
        assessment_service.redis_client.get_session_state.return_value = mock_redis_state

        result = await assessment_service.resume_session(
            session_id="session-123",
            student_id="student-123",
        )

        assert result["success"] is True
        assert result["current_question_id"] == "question-456"
        assert result["questions_answered"] == 10

    @pytest.mark.asyncio
    async def test_resume_session_no_redis_state(self, assessment_service):
        """Session resume fails when no Redis state exists."""
        assessment_service.redis_client.get_session_state = MagicMock()
        assessment_service.redis_client.get_session_state.return_value = None

        with pytest.raises(ValueError, match="Session state not found"):
            await assessment_service.resume_session(
                session_id="session-123",
                student_id="student-123",
            )

    @pytest.mark.asyncio
    async def test_resume_session_invalid_student(self, assessment_service):
        """Session resume validates student matches session."""
        mock_redis_state = {
            "assessment_id": "assessment-123",
            "session_id": "session-123",
            "student_id": "other-student",
        }

        assessment_service.redis_client.get_session_state = MagicMock()
        assessment_service.redis_client.get_session_state.return_value = mock_redis_state

        with pytest.raises(ValueError, match="Session does not belong to student"):
            await assessment_service.resume_session(
                session_id="session-123",
                student_id="student-123",
            )


class TestSessionPersistence:
    """Test session state persistence to Redis."""

    @pytest.fixture
    async def mock_redis_client(self):
        """Create mock Redis client."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_save_question_response(self, mock_redis_client):
        """Question response is persisted to Redis."""
        from src.core.redis_client import save_question_response

        save_question_response(
            redis_client=mock_redis_client,
            session_id="session-123",
            question_id="question-456",
            answer="A",
            is_correct=True,
            timestamp=datetime.utcnow(),
        )

        mock_redis_client.save_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_bkt_state(self, mock_redis_client):
        """BKT state is persisted to Redis."""
        from src.core.redis_client import save_bkt_state

        save_bkt_state(
            redis_client=mock_redis_client,
            session_id="session-123",
            skill_id="4.NBT.A.1",
            p_mastery=0.75,
        )

        mock_redis_client.save_bkt_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_cat_state(self, mock_redis_client):
        """CAT state is persisted to Redis."""
        from src.core.redis_client import save_cat_state

        save_cat_state(
            redis_client=mock_redis_client,
            session_id="session-123",
            theta=0.5,
            covered_standards={"4.NBT.A.1": True},
        )

        mock_redis_client.save_cat_state.assert_called_once()


class TestSessionTimeout:
    """Test session timeout handling."""

    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def assessment_service(self, mock_db_session):
        """Create assessment service."""
        from src.services.assessment_service import AssessmentService
        from src.repositories.assessment_repository import AssessmentRepository
        from src.repositories.session_repository import AssessmentSessionRepository
        from src.repositories.student_repository import StudentRepository
        from src.repositories.standard_repository import StandardRepository
        from src.repositories.question_repository import QuestionRepository
        from src.repositories.consent_repository import ConsentRepository
        from src.services.bkt_service import BKTServiceservice
        from src.services.cat_service import CATService
        from src.core.redis_client import get_redis_client

        assessment_repo = AssessmentRepository(mock_db_session)
        session_repo = AssessmentSessionRepository(mock_db_session)
        student_repo = StudentRepository(mock_db_session)
        standard_repo = StandardRepository(mock_db_session)
        question_repo = QuestionRepository(mock_db_session)
        consent_repo = ConsentRepository(mock_db_session)
        bkt_service = BKTServiceservice()
        cat_service = CATService()
        redis_client = get_redis_client()

        return AssessmentService(
            assessment_repository=assessment_repo,
            session_repository=session_repo,
            student_repository=student_repo,
            standard_repository=standard_repo,
            question_repository=question_repo,
            consent_repository=consent_repo,
            bkt_service=bkt_service,
            cat_service=cat_service,
            redis_client=redis_client,
        )

    @pytest.mark.asyncio
    async def test_session_expired(self, assessment_service):
        """Session is marked abandoned after timeout."""
        # Mock Redis state with old timestamp
        old_time = datetime.utcnow() - timedelta(hours=3)
        mock_redis_state = {
            "assessment_id": "assessment-123",
            "session_id": "session-123",
            "started_at": old_time.isoformat(),
        }

        assessment_service.redis_client.get_session_state = MagicMock()
        assessment_service.redis_client.get_session_state.return_value = mock_redis_state

        # Mock session update
        assessment_service.session_repository.update_session_status = MagicMock()

        result = await assessment_service.check_session_timeout(
            session_id="session-123",
            timeout_minutes=60,
        )

        assert result["expired"] is True
        assessment_service.session_repository.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_not_expired(self, assessment_service):
        """Session is still valid within timeout."""
        # Mock Redis state with recent timestamp
        recent_time = datetime.utcnow() - timedelta(minutes=15)
        mock_redis_state = {
            "assessment_id": "assessment-123",
            "session_id": "session-123",
            "started_at": recent_time.isoformat(),
        }

        assessment_service.redis_client.get_session_state = MagicMock()
        assessment_service.redis_client.get_session_state.return_value = mock_redis_state

        result = await assessment_service.check_session_timeout(
            session_id="session-123",
            timeout_minutes=60,
        )

        assert result["expired"] is False


class TestFullSessionRecoveryFlow:
    """Integration test for complete session recovery flow."""

    @pytest.mark.asyncio
    async def test_pause_resume_complete_flow(self):
        """Complete flow: start -> pause -> resume -> complete."""
        from src.services.assessment_service import AssessmentService
        from src.repositories.assessment_repository import AssessmentRepository
        from src.repositories.session_repository import AssessmentSessionRepository
        from src.repositories.student_repository import StudentRepository
        from src.repositories.standard_repository import StandardRepository
        from src.repositories.question_repository import QuestionRepository
        from src.repositories.consent_repository import ConsentRepository
        from src.services.bkt_service import BKTServiceservice
        from src.services.cat_service import CATService
        from src.core.redis_client import RedisClient
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mocks
        mock_db_session = MagicMock(spec=AsyncSession)
        mock_redis = MagicMock(spec=RedisClient)

        # Create services
        assessment_repo = AssessmentRepository(mock_db_session)
        session_repo = AssessmentSessionRepository(mock_db_session)
        student_repo = StudentRepository(mock_db_session)
        standard_repo = StandardRepository(mock_db_session)
        question_repo = QuestionRepository(mock_db_session)
        consent_repo = ConsentRepository(mock_db_session)
        bkt_service = BKTServiceservice()
        cat_service = CATService()

        assessment_service = AssessmentService(
            assessment_repository=assessment_repo,
            session_repository=session_repo,
            student_repository=student_repo,
            standard_repository=standard_repo,
            question_repository=question_repo,
            consent_repository=consent_repo,
            bkt_service=bkt_service,
            cat_service=cat_service,
            redis_client=mock_redis,
        )

        # Step 1: Start assessment
        mock_assessment = MagicMock()
        mock_assessment.id = "assessment-123"
        mock_session = MagicMock()
        mock_session.id = "session-123"

        assessment_repo.create = MagicMock(return_value=mock_assessment)
        assessment_repo.create_session = MagicMock(return_value=mock_session)

        start_result = await assessment_service.start_assessment(
            student_id="student-123",
            assessment_type="diagnostic",
        )

        assert start_result["assessment_id"] == "assessment-123"
        assert start_result["session_id"] == "session-123"

        # Step 2: Simulate answering some questions
        mock_redis.save_session_state = MagicMock()
        mock_redis.save_question = MagicMock()

        # Answer 10 questions
        for i in range(10):
            mock_redis.save_question(
                session_id="session-123",
                question_id=f"question-{i}",
                answer="A",
                is_correct=i % 2 == 0,
            )

        # Step 3: Pause session
        mock_redis.save_session_state = MagicMock()
        pause_result = await assessment_service.pause_session(
            session_id="session-123",
            student_id="student-123",
        )

        assert pause_result["success"] is True

        # Step 4: Resume session (simulate browser reopen)
        mock_redis.get_session_state = MagicMock(
            return_value={
                "assessment_id": "assessment-123",
                "session_id": "session-123",
                "current_question_id": "question-10",
                "questions_answered": 10,
                "answers": [],
                "bkt_states": {},
                "cat_state": {"theta": 0.3},
                "started_at": datetime.utcnow().isoformat(),
            }
        )

        resume_result = await assessment_service.resume_session(
            session_id="session-123",
            student_id="student-123",
        )

        assert resume_result["success"] is True
        assert resume_result["current_question_id"] == "question-10"
        assert resume_result["questions_answered"] == 10

        # Step 5: Continue and complete
        mock_redis.get_session_state = MagicMock(
            return_value={
                "assessment_id": "assessment-123",
                "session_id": "session-123",
                "current_question_id": "question-34",
                "questions_answered": 34,
                "answers": [],
                "bkt_states": {},
                "cat_state": {"theta": 0.5},
                "started_at": datetime.utcnow().isoformat(),
            }
        )
        mock_redis.get_question_pool = MagicMock(return_value=[])
        mock_redis.delete_session_state = MagicMock()

        complete_result = await assessment_service.complete_assessment(
            assessment_id="assessment-123",
            db_session=mock_db_session,
        )

        assert complete_result["status"] == "completed"
        assert complete_result["total_questions"] == 35
