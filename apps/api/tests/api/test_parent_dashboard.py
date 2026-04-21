"""
Tests for Parent Dashboard endpoints.
"""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import date, timedelta, datetime
import json

from src.main import app
from src.models.models import User, Student, LearningPlan
from src.core.encryption import EncryptionService


@pytest.mark.asyncio
class TestParentDashboard:
    """Tests for parent dashboard endpoints."""

    def test_get_notification_preferences(self, test_api_client, mock_jwt_as_parent):
        """PDT-001: Parent can view their notification preferences."""
        client, _ = test_api_client
        response = client.get(
            "/api/v1/parents/parent-1/preferences",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            assert "email_weekly_summary" in data
            assert "email_milestone_achievements" in data
            assert "sms_reminders" in data
            assert "notification_frequency" in data

    def test_update_notification_preferences(self, test_api_client, mock_jwt_as_parent):
        """PDT-002: Parent can update their notification preferences."""
        client, _ = test_api_client
        response = client.put(
            "/api/v1/parents/parent-1/preferences",
            headers={"Authorization": "Bearer mock-token"},
            json={
                "email_weekly_summary": False,
                "sms_reminders": True,
                "notification_frequency": "daily",
            },
        )

        assert response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            assert data["email_weekly_summary"] is False
            assert data["sms_reminders"] is True
            assert data["notification_frequency"] == "daily"

    def test_parent_dashboard_unauthorized_access(self, test_api_client, mock_jwt_as_teacher):
        """PDT-003: Teacher cannot access parent dashboard."""
        client, _ = test_api_client
        response = client.get(
            "/api/v1/parents/parent-1/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 403

    def test_parent_dashboard_no_children_empty(self, test_api_client, mock_jwt_as_parent):
        """PDT-004: Dashboard works when no children exist."""
        client, engine = test_api_client
        from sqlalchemy import text

        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (id, auth0_id, first_name, last_name, role, is_active, email_hash) "
                     "VALUES (:id, :auth0_id, :first_name, :last_name, :role, :is_active, :email_hash)"),
                {
                    "id": parent_id,
                    "auth0_id": "auth0|test_parent",
                    "first_name": "Test",
                    "last_name": "Parent",
                    "role": "parent",
                    "is_active": True,
                    "email_hash": email_hash
                }
            )
            conn.commit()

        response = client.get(
            f"/api/v1/parents/{parent_id}/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "children" in data

    def test_get_detailed_report_no_data(self, test_api_client, mock_jwt_as_parent):
        """PDT-005: Report endpoint returns valid structure with no data."""
        client, engine = test_api_client
        from sqlalchemy import text

        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (id, auth0_id, first_name, last_name, role, is_active, email_hash) "
                     "VALUES (:id, :auth0_id, :first_name, :last_name, :role, :is_active, :email_hash)"),
                {
                    "id": parent_id,
                    "auth0_id": "auth0|test_parent",
                    "first_name": "Test",
                    "last_name": "Parent",
                    "role": "parent",
                    "is_active": True,
                    "email_hash": email_hash
                }
            )
            conn.commit()

        response = client.get(
            f"/api/v1/parents/{parent_id}/report",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "children" in data


@pytest.mark.asyncio
class TestParentDashboardWithChildren:
    """Tests for parent dashboard with children data."""

    def test_parent_dashboard_with_children(self, test_api_client, mock_jwt_as_parent):
        """PDT-006: Dashboard shows children with learning plans.

        Note: This test verifies that children are returned when no learning plans exist.
        Full learning plan data requires additional setup that would involve creating
        plan_modules with valid standard references.
        """
        client, engine = test_api_client
        from sqlalchemy import text

        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        with engine.connect() as conn:
            # Create parent
            conn.execute(
                text("INSERT INTO users (id, auth0_id, first_name, last_name, role, is_active, email_hash) "
                     "VALUES (:id, :auth0_id, :first_name, :last_name, :role, :is_active, :email_hash)"),
                {
                    "id": parent_id,
                    "auth0_id": "auth0|test_parent",
                    "first_name": "Test",
                    "last_name": "Parent",
                    "role": "parent",
                    "is_active": True,
                    "email_hash": email_hash
                }
            )
            conn.commit()

            # Create student
            student_id = str(uuid4())
            conn.execute(
                text("INSERT INTO students (id, parent_id, grade_level, display_name, is_active) "
                     "VALUES (:id, :parent_id, :grade_level, :display_name, :is_active)"),
                {
                    "id": student_id,
                    "parent_id": parent_id,
                    "grade_level": 4,
                    "display_name": "Test Student",
                    "is_active": True
                }
            )
            conn.commit()

        response = client.get(
            f"/api/v1/parents/{parent_id}/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["children"]) == 1
        child = data["children"][0]
        assert child["name"] == "Test Student"
        assert child["grade"] == 4

    def test_parent_dashboard_multiple_children(self, test_api_client, mock_jwt_as_parent):
        """PDT-007: Dashboard works with multiple children."""
        client, engine = test_api_client
        from sqlalchemy import text

        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        with engine.connect() as conn:
            # Create parent
            conn.execute(
                text("INSERT INTO users (id, auth0_id, first_name, last_name, role, is_active, email_hash) "
                     "VALUES (:id, :auth0_id, :first_name, :last_name, :role, :is_active, :email_hash)"),
                {
                    "id": parent_id,
                    "auth0_id": "auth0|test_parent",
                    "first_name": "Test",
                    "last_name": "Parent",
                    "role": "parent",
                    "is_active": True,
                    "email_hash": email_hash
                }
            )
            conn.commit()

            # Create two students
            for i in range(2):
                student_id = str(uuid4())
                conn.execute(
                    text("INSERT INTO students (id, parent_id, grade_level, display_name, is_active) "
                         "VALUES (:id, :parent_id, :grade_level, :display_name, :is_active)"),
                    {
                        "id": student_id,
                        "parent_id": parent_id,
                        "grade_level": i + 1,
                        "display_name": f"Child {i + 1}",
                        "is_active": True
                    }
                )
            conn.commit()

        response = client.get(
            f"/api/v1/parents/{parent_id}/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["children"]) == 2
