"""Tests for assessment API endpoints."""

import pytest
from unittest.mock import patch, MagicMock


class TestStartAssessmentEndpoint:
    """Test POST /assessments endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "parent-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock assessment service."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.start_assessment = MagicMock()
            mock_service.start_assessment.return_value = {
                "assessment_id": "assessment-123",
                "session_id": "session-456",
                "student_id": "student-123",
                "assessment_type": "diagnostic",
                "status": "in_progress",
                "target_question_count": 35,
                "started_at": "2026-04-14T12:00:00",
            }
            mock.return_value = mock_service
            yield mock_service

    def test_start_assessment_success(self, client, mock_jwt, mock_service):
        """start_assessment returns 201 on success."""
        response = client.post(
            "/api/v1/assessments",
            json={
                "student_id": "student-123",
                "assessment_type": "diagnostic",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["assessment_id"] == "assessment-123"
        assert data["session_id"] == "session-456"
        assert data["status"] == "in_progress"
        mock_service.start_assessment.assert_called_once()

    def test_start_assessment_no_consent(self, client, mock_jwt, mock_service):
        """start_assessment returns 403 without consent."""
        mock_service.start_assessment.side_effect = ValueError(
            "Active COPPA consent required"
        )

        response = client.post(
            "/api/v1/assessments",
            json={
                "student_id": "student-123",
                "assessment_type": "diagnostic",
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    def test_start_assessment_student_not_found(self, client, mock_jwt, mock_service):
        """start_assessment returns 400 for missing student."""
        mock_service.start_assessment.side_effect = ValueError("Student not found")

        response = client.post(
            "/api/v1/assessments",
            json={
                "student_id": "missing-student",
                "assessment_type": "diagnostic",
            },
        )

        assert response.status_code == 400

    def test_start_assessment_active_exists(self, client, mock_jwt, mock_service):
        """start_assessment returns 400 for active assessment."""
        mock_service.start_assessment.side_effect = ValueError(
            "already has an active diagnostic assessment"
        )

        response = client.post(
            "/api/v1/assessments",
            json={
                "student_id": "student-123",
                "assessment_type": "diagnostic",
            },
        )

        assert response.status_code == 400


class TestGetNextQuestionEndpoint:
    """Test GET /assessments/{id}/next-question endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "parent-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock assessment service."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.get_next_question = MagicMock()
            mock_service.get_next_question.return_value = {
                "question": {
                    "question_id": "q1",
                    "question_number": 1,
                    "standard_domain": "Numbers and Operations",
                    "stem": "What is 1234 rounded to the nearest hundred?",
                    "options": [
                        {"key": "A", "text": "1200", "image_url": None},
                        {"key": "B", "text": "1250", "image_url": None},
                        {"key": "C", "text": "1300", "image_url": None},
                        {"key": "D", "text": "1400", "image_url": None},
                    ],
                    "question_type": "multiple_choice",
                },
                "should_end": False,
                "progress": {
                    "questions_answered": 1,
                    "target_total": 35,
                    "domains_covered": {},
                    "estimated_time_remaining_min": 10,
                },
            }
            mock.return_value = mock_service
            yield mock_service

    def test_get_next_question_success(self, client, mock_jwt, mock_service):
        """get_next_question returns 200 with question."""
        response = client.get("/api/v1/assessments/assessment-123/next-question")

        assert response.status_code == 200
        data = response.json()
        assert data["question"]["question_id"] == "q1"
        assert data["question"]["question_number"] == 1
        assert data["should_end"] is False
        mock_service.get_next_question.assert_called_once()

    def test_get_next_question_assessment_not_found(
        self, client, mock_jwt, mock_service
    ):
        """get_next_question returns 400 for missing assessment."""
        mock_service.get_next_question.side_effect = ValueError(
            "Assessment state not found"
        )

        response = client.get(
            "/api/v1/assessments/missing-assessment/next-question"
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestSubmitResponseEndpoint:
    """Test POST /assessments/{id}/responses endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "parent-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock assessment service."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.submit_response = MagicMock()
            mock_service.submit_response.return_value = {
                "is_correct": True,
                "correct_answer": "A",
                "explanation": "1234 rounded to nearest hundred is 1200.",
                "progress": {
                    "questions_answered": 1,
                    "target_total": 35,
                    "domains_covered": {"4.NBT": 1},
                    "estimated_time_remaining_min": 10,
                },
            }
            mock.return_value = mock_service
            yield mock_service

    def test_submit_response_success(self, client, mock_jwt, mock_service):
        """submit_response returns 200 with result."""
        response = client.post(
            "/api/v1/assessments/assessment-123/responses",
            json={
                "question_id": "q1",
                "selected_answer": "A",
                "time_spent_ms": 30000,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["progress"]["questions_answered"] == 1
        mock_service.submit_response.assert_called_once()

    def test_submit_response_question_mismatch(
        self, client, mock_jwt, mock_service
    ):
        """submit_response returns 400 for question mismatch."""
        mock_service.submit_response.side_effect = ValueError(
            "Question mismatch"
        )

        response = client.post(
            "/api/v1/assessments/assessment-123/responses",
            json={
                "question_id": "wrong-question",
                "selected_answer": "A",
                "time_spent_ms": 30000,
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestCompleteAssessmentEndpoint:
    """Test PUT /assessments/{id}/complete endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "parent-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock assessment service."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.complete_assessment = MagicMock()
            mock_service.complete_assessment.return_value = {
                "assessment_id": "assessment-123",
                "status": "completed",
                "total_questions": 35,
                "total_correct": 28,
                "overall_score": 0.8,
                "duration_minutes": 52,
                "completed_at": "2026-04-14T13:00:00",
                "results_url": "/diagnostic/results?assessment=assessment-123",
            }
            mock.return_value = mock_service
            yield mock_service

    def test_complete_assessment_success(self, client, mock_jwt, mock_service):
        """complete_assessment returns 200 with results."""
        response = client.put("/api/v1/assessments/assessment-123/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_questions"] == 35
        assert data["overall_score"] == 0.8
        mock_service.complete_assessment.assert_called_once()

    def test_complete_assessment_insufficient_questions(
        self, client, mock_jwt, mock_service
    ):
        """complete_assessment returns 400 for < 35 questions."""
        mock_service.complete_assessment.side_effect = ValueError(
            "Minimum 35 questions required"
        )

        response = client.put("/api/v1/assessments/assessment-123/complete")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestGetResultsEndpoint:
    """Test GET /assessments/{id}/results endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        from starlette.testclient import TestClient
        return TestClient(app)

    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT validation."""
        with patch("src.core.security.verify_jwt") as mock:
            mock.return_value = {
                "sub": "parent-123",
                "email": "parent@example.com",
                "email_verified": True,
            }
            yield mock

    @pytest.fixture
    def mock_service(self):
        """Mock assessment service."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.get_results = MagicMock()
            mock_service.get_results.return_value = {
                "assessment_id": "assessment-123",
                "student_name": "John Doe",
                "assessment_type": "diagnostic",
                "completed_at": "2026-04-14T13:00:00",
                "overall_score": 0.8,
                "total_questions": 35,
                "total_correct": 28,
                "overall_classification": "above_par",
                "domain_results": [
                    {
                        "domain_code": "4.NBT",
                        "domain_name": "Numbers and Operations",
                        "questions_count": 8,
                        "correct_count": 7,
                        "score": 0.875,
                        "classification": "above_par",
                    }
                ],
                "skill_states": [
                    {
                        "standard_code": "4.NBT.A.1",
                        "standard_title": "Place Value",
                        "p_mastery": 0.85,
                        "mastery_level": "high",
                        "questions_attempted": 3,
                        "questions_correct": 3,
                    }
                ],
                "gap_analysis": {
                    "strengths": ["4.NBT.A.1"],
                    "on_track": ["4.NF.A.1"],
                    "needs_work": ["4.OA.A.1"],
                    "recommended_focus_order": ["4.OA.A.1"],
                },
            }
            mock.return_value = mock_service
            yield mock_service

    def test_get_results_success(self, client, mock_jwt, mock_service):
        """get_results returns 200 with full results."""
        response = client.get("/api/v1/assessments/assessment-123/results")

        assert response.status_code == 200
        data = response.json()
        assert data["assessment_id"] == "assessment-123"
        assert data["student_name"] == "John Doe"
        assert data["overall_score"] == 0.8
        assert "domain_results" in data
        assert "skill_states" in data
        assert "gap_analysis" in data
        mock_service.get_results.assert_called_once()

    def test_get_results_not_found(self, client, mock_jwt, mock_service):
        """get_results returns 404 for missing assessment."""
        mock_service.get_results.side_effect = ValueError(
            "Assessment not found"
        )

        response = client.get("/api/v1/assessments/missing-results/results")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_results_not_completed(
        self, client, mock_jwt, mock_service
    ):
        """get_results returns 403 for incomplete assessment."""
        mock_service.get_results.side_effect = ValueError(
            "Assessment not completed"
        )

        response = client.get("/api/v1/assessments/assessment-123/results")

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    def test_get_results_access_denied(self, client, mock_jwt, mock_service):
        """get_results returns 403 for wrong student."""
        mock_service.get_results.side_effect = ValueError("Access denied")

        response = client.get("/api/v1/assessments/assessment-123/results")

        assert response.status_code == 403
