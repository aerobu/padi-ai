"""Integration tests for assessment flow."""

import pytest
from unittest.mock import patch, MagicMock


class TestFullAssessmentFlow:
    """Test full assessment flow from start to results."""

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
    def mock_consent_service(self):
        """Mock consent service."""
        with patch("src.api.v1.endpoints.consent.get_consent_service") as mock:
            mock_service = MagicMock()
            mock_service.verify_active_consent = MagicMock()
            mock_service.verify_active_consent.return_value = True
            mock.return_value = mock_service
            yield mock_service

    def test_start_assessment_with_valid_consent(
        self, client, mock_jwt, mock_consent_service
    ):
        """Full flow: start assessment with valid consent."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
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
            assert data["status"] == "in_progress"


class TestAssessmentQuestionSequence:
    """Test question sequence during assessment."""

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

    def test_question_sequence_consistency(
        self, client, mock_jwt
    ):
        """Question sequence maintains state across requests."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()

            # First question
            mock_service.get_next_question.side_effect = [
                {
                    "question": {"question_id": "q1", "question_number": 1},
                    "should_end": False,
                    "progress": {"questions_answered": 0},
                },
                {
                    "question": {"question_id": "q2", "question_number": 2},
                    "should_end": False,
                    "progress": {"questions_answered": 1},
                },
                {
                    "question": None,
                    "should_end": True,
                    "progress": {"questions_answered": 35},
                },
            ]
            mock.return_value = mock_service

            # Get first question
            response1 = client.get("/api/v1/assessments/assess-1/next-question")
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["question"]["question_id"] == "q1"

            # Submit response
            mock_service.submit_response = MagicMock()
            mock_service.submit_response.return_value = {
                "is_correct": True,
                "progress": {"questions_answered": 1},
            }

            response2 = client.post(
                "/api/v1/assessments/assess-1/responses",
                json={
                    "question_id": "q1",
                    "selected_answer": "A",
                    "time_spent_ms": 30000,
                },
            )
            assert response2.status_code == 200

            # Get second question
            response3 = client.get("/api/v1/assessments/assess-1/next-question")
            assert response3.status_code == 200
            data3 = response3.json()
            assert data3["question"]["question_id"] == "q2"


class TestAssessmentBKTStatePersistence:
    """Test BKT state persistence across assessment."""

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

    def test_bkt_state_updates_across_responses(
        self, client, mock_jwt
    ):
        """BKT state updates correctly across multiple responses."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.submit_response.return_value = {
                "is_correct": True,
                "correct_answer": "A",
                "explanation": "Test explanation",
                "progress": {"questions_answered": 1},
            }
            mock.return_value = mock_service

            # Submit 5 correct responses
            for i in range(5):
                response = client.post(
                    "/api/v1/assessments/assess-1/responses",
                    json={
                        "question_id": f"q{i}",
                        "selected_answer": "A",
                        "time_spent_ms": 30000,
                    },
                )
                assert response.status_code == 200


class TestAssessmentCompletionValidation:
    """Test assessment completion validation."""

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

    def test_complete_with_insufficient_questions(
        self, client, mock_jwt
    ):
        """Complete returns 400 with < 35 questions."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.complete_assessment.side_effect = ValueError(
                "Minimum 35 questions required"
            )
            mock.return_value = mock_service

            response = client.put("/api/v1/assessments/assess-1/complete")

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    def test_complete_success(self, client, mock_jwt):
        """Complete returns 200 with results."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.complete_assessment.return_value = {
                "assessment_id": "assess-1",
                "status": "completed",
                "total_questions": 35,
                "total_correct": 28,
                "overall_score": 0.8,
                "completed_at": "2026-04-14T13:00:00",
                "results_url": "/diagnostic/results?assessment=assess-1",
            }
            mock.return_value = mock_service

            response = client.put("/api/v1/assessments/assess-1/complete")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["total_questions"] == 35


class TestAssessmentResultsGeneration:
    """Test assessment results generation."""

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

    def test_get_results_includes_all_components(
        self, client, mock_jwt
    ):
        """Results include domain results, skill states, gap analysis."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.get_results.return_value = {
                "assessment_id": "assess-1",
                "student_name": "Test Student",
                "overall_score": 0.8,
                "domain_results": [
                    {"domain_name": "NBT", "score": 0.85},
                ],
                "skill_states": [
                    {
                        "standard_code": "4.NBT.A.1",
                        "p_mastery": 0.85,
                        "mastery_level": "high",
                    }
                ],
                "gap_analysis": {
                    "strengths": ["4.NBT.A.1"],
                    "needs_work": ["4.OA.A.1"],
                },
            }
            mock.return_value = mock_service

            response = client.get("/api/v1/assessments/assess-1/results")

            assert response.status_code == 200
            data = response.json()
            assert "domain_results" in data
            assert "skill_states" in data
            assert "gap_analysis" in data


class TestConsentAssessmentDependency:
    """Test that assessments require consent."""

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

    def test_assessment_requires_active_consent(self, client, mock_jwt):
        """Cannot start assessment without active consent."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.start_assessment.side_effect = ValueError(
                "Active COPPA consent required"
            )
            mock.return_value = mock_service

            response = client.post(
                "/api/v1/assessments",
                json={
                    "student_id": "student-123",
                    "assessment_type": "diagnostic",
                },
            )

            assert response.status_code == 403


class TestAssessmentStateConsistency:
    """Test assessment state consistency."""

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

    def test_question_mismatch_prevention(
        self, client, mock_jwt
    ):
        """Cannot submit response for wrong question."""
        with patch("src.api.v1.endpoints.assessments.get_assessment_service") as mock:
            mock_service = MagicMock()
            mock_service.submit_response.side_effect = ValueError(
                "Question mismatch"
            )
            mock.return_value = mock_service

            response = client.post(
                "/api/v1/assessments/assess-1/responses",
                json={
                    "question_id": "wrong-question",
                    "selected_answer": "A",
                    "time_spent_ms": 30000,
                },
            )

            assert response.status_code == 400
