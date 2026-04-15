"""Tests for assessment service."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestAssessmentServiceInitialization:
    """Test AssessmentService initialization."""

    def test_assessment_service_initialization(self):
        """AssessmentService initializes with all repositories."""
        from src.services.assessment_service import AssessmentService

        # Create mock repositories
        mock_assessment_repo = MagicMock()
        mock_session_repo = MagicMock()
        mock_student_repo = MagicMock()
        mock_standard_repo = MagicMock()
        mock_question_repo = MagicMock()
        mock_consent_repo = MagicMock()
        mock_bkt_service = MagicMock()
        mock_cat_service = MagicMock()
        mock_redis_client = MagicMock()

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=mock_session_repo,
            student_repository=mock_student_repo,
            standard_repository=mock_standard_repo,
            question_repository=mock_question_repo,
            consent_repository=mock_consent_repo,
            bkt_service=mock_bkt_service,
            cat_service=mock_cat_service,
            redis_client=mock_redis_client,
        )

        assert service.TARGET_QUESTION_COUNT == 35
        assert service.assessment_repository == mock_assessment_repo


class TestAssessmentServiceStartAssessment:
    """Test AssessmentService.start_assessment method."""

    @pytest.mark.asyncio
    async def test_start_assessment_success(self):
        """start_assessment creates assessment and session."""
        from src.services.assessment_service import AssessmentService

        # Create mock objects
        mock_student = MagicMock()
        mock_student.id = "student-123"
        mock_student.parent_id = "parent-123"
        mock_student.grade_level = 4

        mock_assessment = MagicMock()
        mock_assessment.id = "assessment-123"

        mock_session = MagicMock()
        mock_session.id = "session-456"

        mock_bkt_state = MagicMock()
        mock_bkt_state.p_mastery = 0.5

        # Setup mocks
        mock_assessment_repo = MagicMock()
        mock_assessment_repo.get_active_diagnostic = MagicMock()
        mock_assessment_repo.get_active_diagnostic.return_value = None
        mock_assessment_repo.create = MagicMock()
        mock_assessment_repo.create.return_value = mock_assessment
        mock_assessment_repo.create_session = MagicMock()
        mock_assessment_repo.create_session.return_value = mock_session

        mock_session_repo = MagicMock()

        mock_student_repo = MagicMock()
        mock_student_repo.get_by_id = MagicMock()
        mock_student_repo.get_by_id.return_value = mock_student

        mock_standard_repo = MagicMock()

        mock_question_repo = MagicMock()
        mock_question_repo.get_available_questions = MagicMock()
        mock_question_repo.get_available_questions.return_value = []

        mock_consent_repo = MagicMock()
        mock_consent_repo.has_active_consent = MagicMock()
        mock_consent_repo.has_active_consent.return_value = True

        mock_bkt_service = MagicMock()

        mock_cat_service = MagicMock()
        mock_cat_state = MagicMock()
        mock_cat_state.theta = 0.0
        mock_cat_state.covered_standards = {}
        mock_cat_service.initialize_assessment = MagicMock()
        mock_cat_service.initialize_assessment.return_value = mock_cat_state
        mock_cat_service.get_progress = MagicMock()
        mock_cat_service.get_progress.return_value = {"questions_answered": 0}

        mock_redis_client = MagicMock()

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=mock_session_repo,
            student_repository=mock_student_repo,
            standard_repository=mock_standard_repo,
            question_repository=mock_question_repo,
            consent_repository=mock_consent_repo,
            bkt_service=mock_bkt_service,
            cat_service=mock_cat_service,
            redis_client=mock_redis_client,
        )

        result = await service.start_assessment(
            student_id="student-123",
            assessment_type="diagnostic",
        )

        assert result["assessment_id"] == "assessment-123"
        assert result["session_id"] == "session-456"
        assert result["student_id"] == "student-123"
        assert result["assessment_type"] == "diagnostic"
        assert result["status"] == "in_progress"
        assert result["target_question_count"] == 35

    @pytest.mark.asyncio
    async def test_start_assessment_student_not_found(self):
        """start_assessment raises error for missing student."""
        from src.services.assessment_service import AssessmentService

        mock_assessment_repo = MagicMock()
        mock_session_repo = MagicMock()
        mock_student_repo = MagicMock()
        mock_student_repo.get_by_id = MagicMock()
        mock_student_repo.get_by_id.return_value = None

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=mock_session_repo,
            student_repository=mock_student_repo,
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        with pytest.raises(ValueError, match="Student not found"):
            await service.start_assessment(
                student_id="missing-student",
                assessment_type="diagnostic",
            )

    @pytest.mark.asyncio
    async def test_start_assessment_no_consent(self):
        """start_assessment raises error without consent."""
        from src.services.assessment_service import AssessmentService

        mock_student = MagicMock()
        mock_student.parent_id = "parent-123"

        mock_assessment_repo = MagicMock()
        mock_session_repo = MagicMock()
        mock_student_repo = MagicMock()
        mock_student_repo.get_by_id = MagicMock()
        mock_student_repo.get_by_id.return_value = mock_student

        mock_consent_repo = MagicMock()
        mock_consent_repo.has_active_consent = MagicMock()
        mock_consent_repo.has_active_consent.return_value = False

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=mock_session_repo,
            student_repository=mock_student_repo,
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=mock_consent_repo,
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        with pytest.raises(ValueError, match="Active COPPA consent required"):
            await service.start_assessment(
                student_id="student-123",
                assessment_type="diagnostic",
            )

    @pytest.mark.asyncio
    async def test_start_assessment_active_assessment_exists(self):
        """start_assessment raises error when active assessment exists."""
        from src.services.assessment_service import AssessmentService

        mock_student = MagicMock()
        mock_student.parent_id = "parent-123"

        mock_active_assessment = MagicMock()

        mock_assessment_repo = MagicMock()
        mock_assessment_repo.get_active_diagnostic = MagicMock()
        mock_assessment_repo.get_active_diagnostic.return_value = mock_active_assessment

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        with pytest.raises(ValueError, match="already has an active"):
            await service.start_assessment(
                student_id="student-123",
                assessment_type="diagnostic",
            )


class TestAssessmentServiceGetNextQuestion:
    """Test AssessmentService.get_next_question method."""

    @pytest.mark.asyncio
    async def test_get_next_question_success(self):
        """get_next_question returns question."""
        from src.services.assessment_service import AssessmentService

        mock_student = MagicMock()
        mock_student.grade_level = 4

        mock_assessment = MagicMock()
        mock_assessment.id = "assessment-123"

        mock_question = {
            "id": "q1",
            "standard_code": "4.NBT.A.1",
            "difficulty": 3,
            "is_active": True,
        }

        mock_bkt_state = MagicMock()

        mock_cat_service = MagicMock()
        mock_cat_service.select_next_question = MagicMock()
        mock_cat_service.select_next_question.return_value = mock_question
        mock_cat_service.get_progress = MagicMock()
        mock_cat_service.get_progress.return_value = {
            "questions_answered": 1,
            "target_total": 35,
        }

        mock_redis_client = MagicMock()
        mock_redis_client.get_assessment_state = MagicMock()
        mock_redis_client.get_assessment_state.return_value = {
            "theta": 0.0,
            "covered_standards": {},
            "questions_answered": 0,
            "session_id": "session-123",
        }
        mock_redis_client.get_question_pool = MagicMock()
        mock_redis_client.get_question_pool.return_value = [mock_question]
        mock_redis_client.set_current_question = MagicMock()

        mock_assessment_repo = MagicMock()
        mock_assessment_repo.get_responses_for_session = MagicMock()
        mock_assessment_repo.get_responses_for_session.return_value = []

        mock_student_repo = MagicMock()
        mock_student_repo.get_by_id = MagicMock()
        mock_student_repo.get_by_id.return_value = mock_student

        mock_question_repo = MagicMock()
        mock_question_repo.get_question_with_options = MagicMock()
        mock_question_repo.get_question_with_options.return_value = {
            "id": "q1",
            "question_text": "Test question?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "opt1", "option_text": "A", "is_correct": True},
                {"id": "opt2", "option_text": "B", "is_correct": False},
            ],
        }

        mock_standard_repo = MagicMock()
        mock_standard = MagicMock()
        mock_standard.domain = "Numbers and Operations"
        mock_standard_repo.get_by_code = MagicMock()
        mock_standard_repo.get_by_code.return_value = mock_standard

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=mock_student_repo,
            standard_repository=mock_standard_repo,
            question_repository=mock_question_repo,
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=mock_cat_service,
            redis_client=mock_redis_client,
        )

        result = await service.get_next_question(
            assessment_id="assessment-123",
            student_id="student-123",
        )

        assert "question" in result
        assert result["question"]["question_id"] == "q1"
        assert result["should_end"] is False

    @pytest.mark.asyncio
    async def test_get_next_question_assessment_not_found(self):
        """get_next_question raises error for missing assessment."""
        from src.services.assessment_service import AssessmentService

        mock_redis_client = MagicMock()
        mock_redis_client.get_assessment_state = MagicMock()
        mock_redis_client.get_assessment_state.return_value = None

        service = AssessmentService(
            assessment_repository=MagicMock(),
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=mock_redis_client,
        )

        with pytest.raises(ValueError, match="Assessment state not found"):
            await service.get_next_question(
                assessment_id="missing-assessment",
                student_id="student-123",
            )

    @pytest.mark.asyncio
    async def test_get_next_question_should_end(self):
        """get_next_question indicates when assessment should end."""
        from src.services.assessment_service import AssessmentService

        mock_redis_client = MagicMock()
        mock_redis_client.get_assessment_state = MagicMock()
        mock_redis_client.get_assessment_state.return_value = {
            "theta": 0.0,
            "covered_standards": {},
            "questions_answered": 35,
            "session_id": "session-123",
        }
        mock_redis_client.get_question_pool = MagicMock()
        mock_redis_client.get_question_pool.return_value = []

        mock_cat_service = MagicMock()
        mock_cat_service.select_next_question = MagicMock()
        mock_cat_service.select_next_question.return_value = None
        mock_cat_service.should_end_assessment = MagicMock()
        mock_cat_service.should_end_assessment.return_value = (True, "max_questions_reached")

        service = AssessmentService(
            assessment_repository=MagicMock(),
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=mock_cat_service,
            redis_client=mock_redis_client,
        )

        result = await service.get_next_question(
            assessment_id="assessment-123",
            student_id="student-123",
        )

        assert result["should_end"] is True
        assert result["end_reason"] == "max_questions_reached"


class TestAssessmentServiceSubmitResponse:
    """Test AssessmentService.submit_response method."""

    @pytest.mark.asyncio
    async def test_submit_response_success(self):
        """submit_response records response and updates BKT."""
        from src.services.assessment_service import AssessmentService

        mock_redis_client = MagicMock()
        mock_redis_client.get_assessment_state = MagicMock()
        mock_redis_client.get_assessment_state.return_value = {
            "theta": 0.0,
            "covered_standards": {},
            "questions_answered": 0,
            "session_id": "session-123",
            "student_id": "student-123",
        }
        mock_redis_client.get_current_question = MagicMock()
        mock_redis_client.get_current_question.return_value = "q1"
        mock_redis_client.save_bkt_state = MagicMock()

        mock_question = MagicMock()
        mock_question.standard_id = "4.NBT.A.1"

        mock_assessment_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_assessment_repo.get_session = MagicMock()
        mock_assessment_repo.get_session.return_value = mock_session
        mock_assessment_repo.record_response = MagicMock()

        mock_question_repo = MagicMock()
        mock_question_repo.get_by_id = MagicMock()
        mock_question_repo.get_by_id.return_value = mock_question
        mock_question_repo.get_question_with_options = MagicMock()
        mock_question_repo.get_question_with_options.return_value = {
            "id": "q1",
            "options": [
                {"id": "opt1", "option_text": "A", "is_correct": True},
            ],
        }

        mock_bkt_service = MagicMock()
        mock_bkt_state = MagicMock()
        mock_bkt_state.p_mastery = 0.6
        mock_bkt_service.update_state = MagicMock()
        mock_bkt_service.update_state.return_value = mock_bkt_state

        mock_cat_service = MagicMock()
        mock_cat_service.get_progress = MagicMock()
        mock_cat_service.get_progress.return_value = {
            "questions_answered": 1,
            "target_total": 35,
        }

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=mock_question_repo,
            consent_repository=MagicMock(),
            bkt_service=mock_bkt_service,
            cat_service=mock_cat_service,
            redis_client=mock_redis_client,
        )

        result = await service.submit_response(
            assessment_id="assessment-123",
            student_id="student-123",
            question_id="q1",
            selected_answer="A",
            time_spent_ms=30000,
        )

        assert result["is_correct"] is True
        assert result["progress"]["questions_answered"] == 1
        mock_assessment_repo.record_response.assert_called_once()


class TestAssessmentServiceCompleteAssessment:
    """Test AssessmentService.complete_assessment method."""

    @pytest.mark.asyncio
    async def test_complete_assessment_success(self):
        """complete_assessment completes assessment and saves BKT states."""
        from src.services.assessment_service import AssessmentService

        mock_responses = [
            MagicMock(is_correct=True),
            MagicMock(is_correct=True),
            MagicMock(is_correct=True),
        ]

        mock_redis_client = MagicMock()
        mock_redis_client.get_assessment_state = MagicMock()
        mock_redis_client.get_assessment_state.return_value = {
            "theta": 0.8,
            "covered_standards": {},
            "questions_answered": 35,
            "session_id": "session-123",
            "student_id": "student-123",
            "bkt_states": {"4.NBT.A.1": {"p_mastery": 0.8}},
        }
        mock_redis_client.delete_assessment_state = MagicMock()

        mock_assessment = MagicMock()
        mock_assessment.id = "assessment-123"
        mock_assessment.student_id = "student-123"
        mock_assessment.status = "in_progress"

        mock_assessment_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_assessment_repo.get_session = MagicMock()
        mock_assessment_repo.get_session.return_value = mock_session
        mock_assessment_repo.get_responses_for_session = MagicMock()
        mock_assessment_repo.get_responses_for_session.return_value = mock_responses
        mock_assessment_repo.complete_session = MagicMock()
        mock_assessment_repo.update_assessment_status = MagicMock()

        mock_db_session = MagicMock()

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=mock_redis_client,
            async_session_factory=mock_db_session,
        )

        result = await service.complete_assessment(
            assessment_id="assessment-123",
            db_session=mock_db_session,
        )

        assert result["status"] == "completed"
        assert result["total_questions"] == 35
        assert "overall_score" in result
        assert "results_url" in result


class TestAssessmentServiceGetResults:
    """Test AssessmentService.get_results method."""

    @pytest.mark.asyncio
    async def test_get_results_success(self):
        """get_results returns assessment results."""
        from src.services.assessment_service import AssessmentService

        mock_responses = [
            MagicMock(is_correct=True),
            MagicMock(is_correct=True),
            MagicMock(is_correct=False),
        ]

        mock_assessment = MagicMock()
        mock_assessment.id = "assessment-123"
        mock_assessment.student_id = "student-123"
        mock_assessment.status = "completed"
        mock_assessment.total_score = 0.67
        mock_assessment.completed_at = datetime.utcnow()

        mock_student = MagicMock()
        mock_student.first_name = "John"
        mock_student.last_name = "Doe"

        mock_assessment_repo = MagicMock()
        mock_assessment_repo.get_by_id = MagicMock()
        mock_assessment_repo.get_by_id.return_value = mock_assessment

        mock_student_repo = MagicMock()
        mock_student_repo.get_by_id = MagicMock()
        mock_student_repo.get_by_id.return_value = mock_student

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=mock_student_repo,
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        result = await service.get_results(
            assessment_id="assessment-123",
            student_id="student-123",
        )

        assert result["assessment_id"] == "assessment-123"
        assert result["student_name"] == "John Doe"
        assert result["overall_score"] == 0.67
        assert result["overall_classification"] == "on_par"
        assert "domain_results" in result
        assert "skill_states" in result
        assert "gap_analysis" in result

    @pytest.mark.asyncio
    async def test_get_results_assessment_not_found(self):
        """get_results raises error for missing assessment."""
        from src.services.assessment_service import AssessmentService

        mock_assessment_repo = MagicMock()
        mock_assessment_repo.get_by_id = MagicMock()
        mock_assessment_repo.get_by_id.return_value = None

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        with pytest.raises(ValueError, match="Assessment not found"):
            await service.get_results(
                assessment_id="missing-assessment",
                student_id="student-123",
            )

    @pytest.mark.asyncio
    async def test_get_results_assessment_not_completed(self):
        """get_results raises error for incomplete assessment."""
        from src.services.assessment_service import AssessmentService

        mock_assessment = MagicMock()
        mock_assessment.status = "in_progress"

        mock_assessment_repo = MagicMock()
        mock_assessment_repo.get_by_id = MagicMock()
        mock_assessment_repo.get_by_id.return_value = mock_assessment

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        with pytest.raises(ValueError, match="Assessment not completed"):
            await service.get_results(
                assessment_id="assessment-123",
                student_id="student-123",
            )

    @pytest.mark.asyncio
    async def test_get_results_access_denied(self):
        """get_results denies access for wrong student."""
        from src.services.assessment_service import AssessmentService

        mock_assessment = MagicMock()
        mock_assessment.student_id = "other-student"
        mock_assessment.status = "completed"

        mock_assessment_repo = MagicMock()
        mock_assessment_repo.get_by_id = MagicMock()
        mock_assessment_repo.get_by_id.return_value = mock_assessment

        service = AssessmentService(
            assessment_repository=mock_assessment_repo,
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        with pytest.raises(ValueError, match="Access denied"):
            await service.get_results(
                assessment_id="assessment-123",
                student_id="student-123",
            )


class TestAssessmentServiceGapAnalysis:
    """Test AssessmentService._generate_gap_analysis method."""

    def test_generate_gap_analysis_classifies_strengths(self):
        """_generate_gap_analysis classifies high mastery as strengths."""
        from src.services.assessment_service import AssessmentService

        service = AssessmentService(
            assessment_repository=MagicMock(),
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        skill_states = [
            {"standard_code": "4.NBT.A.1", "p_mastery": 0.85},
            {"standard_code": "4.NF.A.1", "p_mastery": 0.90},
        ]

        gap_analysis = service._generate_gap_analysis(skill_states)

        assert "4.NBT.A.1" in gap_analysis["strengths"]
        assert "4.NF.A.1" in gap_analysis["strengths"]
        assert len(gap_analysis["needs_work"]) == 0

    def test_generate_gap_analysis_classifies_needs_work(self):
        """_generate_gap_analysis classifies low mastery as needs work."""
        from src.services.assessment_service import AssessmentService

        service = AssessmentService(
            assessment_repository=MagicMock(),
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        skill_states = [
            {"standard_code": "4.NBT.A.1", "p_mastery": 0.30},
            {"standard_code": "4.NF.A.1", "p_mastery": 0.45},
        ]

        gap_analysis = service._generate_gap_analysis(skill_states)

        assert "4.NBT.A.1" in gap_analysis["needs_work"]
        assert "4.NF.A.1" in gap_analysis["needs_work"]
        assert len(gap_analysis["strengths"]) == 0

    def test_generate_gap_analysis_classifies_on_track(self):
        """_generate_gap_analysis classifies medium mastery as on track."""
        from src.services.assessment_service import AssessmentService

        service = AssessmentService(
            assessment_repository=MagicMock(),
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        skill_states = [
            {"standard_code": "4.NBT.A.1", "p_mastery": 0.70},
            {"standard_code": "4.NF.A.1", "p_mastery": 0.65},
        ]

        gap_analysis = service._generate_gap_analysis(skill_states)

        assert "4.NBT.A.1" in gap_analysis["on_track"]
        assert "4.NF.A.1" in gap_analysis["on_track"]

    def test_generate_gap_analysis_recommended_order(self):
        """_generate_gap_analysis orders needs work by impact."""
        from src.services.assessment_service import AssessmentService

        service = AssessmentService(
            assessment_repository=MagicMock(),
            session_repository=MagicMock(),
            student_repository=MagicMock(),
            standard_repository=MagicMock(),
            question_repository=MagicMock(),
            consent_repository=MagicMock(),
            bkt_service=MagicMock(),
            cat_service=MagicMock(),
            redis_client=MagicMock(),
        )

        skill_states = [
            {"standard_code": "4.NBT.A.1", "p_mastery": 0.30},
            {"standard_code": "4.NF.A.1", "p_mastery": 0.20},  # Lower = higher priority
        ]

        gap_analysis = service._generate_gap_analysis(skill_states)

        # Should be ordered by lowest mastery first
        assert gap_analysis["recommended_focus_order"][0] == "4.NF.A.1"


class TestGetAssessmentService:
    """Test singleton assessment service accessor."""

    def test_get_assessment_service_raises_not_initialized(self):
        """get_assessment_service raises error if not initialized."""
        from src.services.assessment_service import get_assessment_service

        with pytest.raises(RuntimeError, match="AssessmentService not initialized"):
            get_assessment_service()

    def test_initialize_assessment_service(self):
        """initialize_assessment_service creates and returns service."""
        from src.services.assessment_service import (
            initialize_assessment_service,
            AssessmentService,
        )
        from src.repositories.assessment_repository import (
            AssessmentRepository,
            AssessmentSessionRepository,
        )
        from src.repositories.student_repository import StudentRepository
        from src.repositories.standard_repository import StandardRepository
        from src.repositories.question_repository import QuestionRepository
        from src.repositories.consent_repository import ConsentRepository
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = MagicMock(spec=AsyncSession)

        service = initialize_assessment_service(
            assessment_repository=AssessmentRepository(mock_session),
            session_repository=AssessmentSessionRepository(mock_session),
            student_repository=StudentRepository(mock_session),
            standard_repository=StandardRepository(mock_session),
            question_repository=QuestionRepository(mock_session),
            consent_repository=ConsentRepository(mock_session),
        )

        assert isinstance(service, AssessmentService)
