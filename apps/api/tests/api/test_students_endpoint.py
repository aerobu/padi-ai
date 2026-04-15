"""Tests for student API endpoints."""

import pytest
from unittest.mock import patch, MagicMock


class TestCreateStudentEndpoint:
    """Test POST /students endpoint."""

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
        """Mock student service."""
        with patch("src.api.v1.endpoints.students.get_student_service") as mock:
            mock_service = MagicMock()
            mock_service.create_student = MagicMock()
            mock_service.create_student.return_value = {
                "student_id": "student-123",
                "display_name": "Test Student",
                "grade_level": 4,
            }
            mock.return_value = mock_service
            yield mock_service

    def test_create_student_success(self, client, mock_jwt, mock_service):
        """create_student returns 201 on success."""
        response = client.post(
            "/api/v1/students",
            json={
                "display_name": "Test Student",
                "grade_level": 4,
                "avatar_id": "avatar_default",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["student_id"] == "student-123"
        assert data["display_name"] == "Test Student"
        mock_service.create_student.assert_called_once()

    def test_create_student_no_consent(self, client, mock_jwt, mock_service):
        """create_student returns 403 without consent."""
        mock_service.create_student.side_effect = ValueError(
            "Active COPPA consent required"
        )

        response = client.post(
            "/api/v1/students",
            json={
                "display_name": "Test Student",
                "grade_level": 4,
            },
        )

        assert response.status_code == 403


class TestListStudentsEndpoint:
    """Test GET /students endpoint."""

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
        """Mock student service."""
        with patch("src.api.v1.endpoints.students.get_student_service") as mock:
            mock_service = MagicMock()
            mock_service.list_students = MagicMock()
            mock_service.list_students.return_value = [
                {
                    "student_id": "student-1",
                    "display_name": "Student 1",
                    "grade_level": 4,
                },
                {
                    "student_id": "student-2",
                    "display_name": "Student 2",
                    "grade_level": 5,
                },
            ]
            mock.return_value = mock_service
            yield mock_service

    def test_list_students_success(self, client, mock_jwt, mock_service):
        """list_students returns 200 with students."""
        response = client.get("/api/v1/students")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["display_name"] == "Student 1"
        mock_service.list_students.assert_called_once()


class TestGetStudentEndpoint:
    """Test GET /students/{id} endpoint."""

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
        """Mock student service."""
        with patch("src.api.v1.endpoints.students.get_student_service") as mock:
            mock_service = MagicMock()
            mock_service.get_student = MagicMock()
            mock_service.get_student.return_value = {
                "student_id": "student-123",
                "display_name": "Test Student",
                "grade_level": 4,
                "created_at": "2026-04-14T00:00:00",
            }
            mock.return_value = mock_service
            yield mock_service

    def test_get_student_success(self, client, mock_jwt, mock_service):
        """get_student returns 200 with student data."""
        response = client.get("/api/v1/students/student-123")

        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "student-123"
        assert data["display_name"] == "Test Student"
        mock_service.get_student.assert_called_once_with("student-123")

    def test_get_student_not_found(self, client, mock_jwt, mock_service):
        """get_student returns 404 for missing student."""
        mock_service.get_student.side_effect = ValueError("Student not found")

        response = client.get("/api/v1/students/missing-student")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestUpdateStudentEndpoint:
    """Test PUT /students/{id} endpoint."""

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
        """Mock student service."""
        with patch("src.api.v1.endpoints.students.get_student_service") as mock:
            mock_service = MagicMock()
            mock_service.update_student = MagicMock()
            mock_service.update_student.return_value = {
                "student_id": "student-123",
                "display_name": "Updated Student",
                "grade_level": 4,
            }
            mock.return_value = mock_service
            yield mock_service

    def test_update_student_success(self, client, mock_jwt, mock_service):
        """update_student returns 200 with updated student."""
        response = client.put(
            "/api/v1/students/student-123",
            json={"display_name": "Updated Student"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Student"
        mock_service.update_student.assert_called_once()

    def test_update_student_not_found(self, client, mock_jwt, mock_service):
        """update_student returns 404 for missing student."""
        mock_service.update_student.side_effect = ValueError("Student not found")

        response = client.put(
            "/api/v1/students/missing-student",
            json={"display_name": "Updated"},
        )

        assert response.status_code == 404
