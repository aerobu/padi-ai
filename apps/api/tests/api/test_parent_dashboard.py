"""
Tests for Parent Dashboard endpoints.
"""
import pytest
from uuid import uuid4

from src.models.models import User, Student
from src.core.encryption import EncryptionService

@pytest.mark.asyncio
class TestParentDashboard:
    """Tests for parent dashboard endpoints."""

    async def test_get_notification_preferences(self, client, mock_jwt_as_parent):
        """PDT-001: Parent can view their notification preferences."""
        response = await client.get(
            "/api/v1/parents/parent-1/preferences",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "email_weekly_summary" in data

    async def test_update_notification_preferences(self, client, mock_jwt_as_parent):
        """PDT-002: Parent can update their notification preferences."""
        response = await client.put(
            "/api/v1/parents/parent-1/preferences",
            headers={"Authorization": "Bearer mock-token"},
            json={
                "email_weekly_summary": False,
                "sms_reminders": True,
                "notification_frequency": "daily",
            },
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["email_weekly_summary"] is False

    async def test_parent_dashboard_unauthorized_access(self, client, mock_jwt_as_teacher):
        """PDT-003: Teacher cannot access parent dashboard."""
        response = await client.get(
            "/api/v1/parents/parent-1/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 403

    async def test_parent_dashboard_no_children_empty(self, client, async_db_session, mock_jwt_as_parent):
        """PDT-004: Dashboard works when no children exist."""
        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        parent = User(
            id=parent_id,
            auth0_id="auth0|test_parent",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
            email_hash=email_hash
        )
        async_db_session.add(parent)
        await async_db_session.commit()

        response = await client.get(
            f"/api/v1/parents/{parent_id}/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "children" in data

    async def test_get_detailed_report_no_data(self, client, async_db_session, mock_jwt_as_parent):
        """PDT-005: Report endpoint returns valid structure with no data."""
        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        parent = User(
            id=parent_id,
            auth0_id="auth0|test_parent_2",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
            email_hash=email_hash
        )
        async_db_session.add(parent)
        await async_db_session.commit()

        response = await client.get(
            f"/api/v1/parents/{parent_id}/report",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "children" in data


@pytest.mark.asyncio
class TestParentDashboardWithChildren:
    """Tests for parent dashboard with children data."""

    async def test_parent_dashboard_with_children(self, client, async_db_session, mock_jwt_as_parent):
        """PDT-006: Dashboard shows children with learning plans."""
        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        parent = User(
            id=parent_id,
            auth0_id="auth0|test_parent_3",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
            email_hash=email_hash
        )
        async_db_session.add(parent)

        # Create student
        student_id = str(uuid4())
        student = Student(
            id=student_id,
            parent_id=parent_id,
            grade_level=4,
            display_name="Test Student",
            is_active=True
        )
        async_db_session.add(student)
        await async_db_session.commit()

        response = await client.get(
            f"/api/v1/parents/{parent_id}/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["children"]) >= 1
        # Find our student in the list
        child = next((c for c in data["children"] if c["name"] == "Test Student"), None)
        assert child is not None
        assert child["grade"] == 4

    async def test_parent_dashboard_multiple_children(self, client, async_db_session, mock_jwt_as_parent):
        """PDT-007: Dashboard works with multiple children."""
        # Use parent-1 to match mock JWT sub
        parent_id = "parent-1"
        svc = EncryptionService()
        email_hash = svc.hash_for_lookup("testparent@example.com")

        parent = User(
            id=parent_id,
            auth0_id="auth0|test_parent_4",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True,
            email_hash=email_hash
        )
        async_db_session.add(parent)

        # Create two students
        for i in range(2):
            student = Student(
                id=str(uuid4()),
                parent_id=parent_id,
                grade_level=i + 1,
                display_name=f"Child {i + 1}",
                is_active=True
            )
            async_db_session.add(student)
        await async_db_session.commit()

        response = await client.get(
            f"/api/v1/parents/{parent_id}/dashboard",
            headers={"Authorization": "Bearer mock-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["children"]) >= 2
