"""
Tests for Student API endpoints.
"""
import pytest
from uuid import uuid4
from datetime import datetime
from src.models.models import Student, ConsentRecord, ConsentStatus, User

@pytest.mark.asyncio
class TestStudentsEndpoints:
    """Tests for student API."""

    async def _seed_parent(self, async_db_session, user_id="test-parent-id"):
        parent = User(
            id=user_id,
            auth0_id=f"auth0|{user_id}",
            first_name="Test",
            last_name="Parent",
            role="parent",
            is_active=True
        )
        parent.set_email(f"{user_id}@example.com")
        async_db_session.add(parent)
        await async_db_session.flush()
        return parent

    async def test_create_student_requires_consent(self, client, async_db_session):
        """API-STD-001: Create student returns 403 if no consent exists."""
        await self._seed_parent(async_db_session)
        await async_db_session.commit()
        
        payload = {
            "display_name": "Jayden",
            "grade_level": 4,
            "avatar_id": "avatar_default"
        }
        response = await client.post("/api/v1/students", json=payload)
        assert response.status_code == 403
        assert "COPPA consent required" in response.json()["detail"]

    async def test_create_student_success(self, client, async_db_session):
        """API-STD-002: Create student succeeds with active consent."""
        await self._seed_parent(async_db_session)
        
        # Seed active consent for test-parent-id
        consent = ConsentRecord(
            id=str(uuid4()),
            user_id="test-parent-id",
            student_id=None,
            consent_type="coppa_verifiable",
            status=ConsentStatus.GRANTED,
            consented_at=datetime.utcnow()
        )
        async_db_session.add(consent)
        await async_db_session.commit()
        
        payload = {
            "display_name": "Jayden",
            "grade_level": 4,
            "avatar_id": "avatar_default"
        }
        response = await client.post("/api/v1/students", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["display_name"] == "Jayden"
        assert "student_id" in data

    async def test_get_student_by_id(self, client, async_db_session):
        """API-STD-003: Verify student can be retrieved by ID."""
        await self._seed_parent(async_db_session)
        
        student_id = str(uuid4())
        student = Student(
            id=student_id,
            parent_id="test-parent-id",
            display_name="Emma",
            grade_level=3,
            is_active=True
        )
        async_db_session.add(student)
        await async_db_session.commit()
        
        response = await client.get(f"/api/v1/students/{student_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Emma"
        assert data["student_id"] == student_id

    async def test_get_student_wrong_owner(self, client, async_db_session):
        """API-STD-004: Accessing another parent's student returns 403."""
        await self._seed_parent(async_db_session, user_id="other-parent-id")
        
        student_id = str(uuid4())
        student = Student(
            id=student_id,
            parent_id="other-parent-id",
            display_name="Not Mine",
            grade_level=4
        )
        async_db_session.add(student)
        await async_db_session.commit()
        
        response = await client.get(f"/api/v1/students/{student_id}")
        assert response.status_code == 403

    async def test_list_students(self, client, async_db_session):
        """API-STD-005: Verify parent can list their own students."""
        await self._seed_parent(async_db_session, user_id="test-parent-id")
        await self._seed_parent(async_db_session, user_id="other-parent-id")
        
        async_db_session.add_all([
            Student(id=str(uuid4()), parent_id="test-parent-id", display_name="S1", grade_level=1),
            Student(id=str(uuid4()), parent_id="test-parent-id", display_name="S2", grade_level=2),
            Student(id=str(uuid4()), parent_id="other-parent-id", display_name="S3", grade_level=3)
        ])
        await async_db_session.commit()
        
        response = await client.get("/api/v1/students")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(s["display_name"] in ["S1", "S2"] for s in data)

    async def test_update_student(self, client, async_db_session):
        """API-STD-006: Verify student can be updated by owner."""
        await self._seed_parent(async_db_session)
        
        student_id = str(uuid4())
        student = Student(
            id=student_id,
            parent_id="test-parent-id",
            display_name="Jayden",
            grade_level=4
        )
        async_db_session.add(student)
        await async_db_session.commit()
        
        payload = {"display_name": "Jayden Updated", "grade_level": 5}
        response = await client.put(f"/api/v1/students/{student_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Jayden Updated"
        assert data["grade_level"] == 5
