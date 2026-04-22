"""
Comprehensive tests for Learning Plans API endpoints.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta
from uuid import uuid4

from src.models.models import LearningPlan, PlanModule, PlanLesson, Student, StudentSkillState, Assessment
from src.services.learning_plan_service import LearningPlanService
from src.services.skill_graph_service import initialize_skill_graph


@pytest_asyncio.fixture(autouse=True)
async def setup_skill_graph(db_session: AsyncSession, seed_grade_4_standards):
    """Automatically initialize the skill graph for all tests in this module."""
    from src.services.skill_graph_service import initialize_skill_graph
    # Standards must be seeded BEFORE graph initialization
    await initialize_skill_graph(db_session)
    yield
    # Clear cache after each test to keep isolation
    from src.services.skill_graph_service import clear_cached_graph
    clear_cache_func = clear_cached_graph
    if callable(clear_cache_func):
        if hasattr(clear_cache_func, '__call__') and not hasattr(clear_cache_func, 'is_async'):
             # If it's a sync function
             clear_cache_func()


class TestLearningPlansGeneration:
    """Tests for POST /api/v1/learning-plans/generate."""

    @pytest.mark.asyncio
    async def test_generate_learning_plan_success(
        self,
        db_session: AsyncSession,
        seed_grade_4_standards,
        test_student: Student,
        test_assessment,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test successful learning plan generation."""
        # Seed skill states since service requires them
        for std in seed_grade_4_standards:
            state = StudentSkillState(
                id=str(uuid4()),
                student_id=test_student.id,
                standard_id=std.id,
                mastery_prob=0.5
            )
            db_session.add(state)
        await db_session.commit()

        response = await client.post(
            "/api/v1/learning-plans/generate",
            json={"student_id": test_student.id, "assessment_id": test_assessment.id},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "plan_id" in data
        assert "track" in data
        assert "total_modules" in data
        assert data["track"] in ["catch_up", "on_track", "accelerate"]

    @pytest.mark.asyncio
    async def test_generate_learning_plan_no_assessment(
        self,
        db_session: AsyncSession,
        test_student_without_assessment: Student,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test generating plan without completed assessment returns error."""
        response = await client.post(
            "/api/v1/learning-plans/generate",
            json={"student_id": test_student_without_assessment.id},
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.skip(
        reason="client fixture installs a default verify_jwt override, so "
               "requests without Authorization headers cannot reach an "
               "unauthenticated state. Needs a separate unauthed_client."
    )
    @pytest.mark.asyncio
    async def test_generate_learning_plan_unauthorized(
        self,
        db_session: AsyncSession,
        test_student: Student,
        client: AsyncClient,
    ):
        """Test generating plan without auth returns 401."""
        response = await client.post(
            "/api/v1/learning-plans/generate",
            json={"student_id": test_student.id},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_learning_plan_permission_denied(
        self,
        db_session: AsyncSession,
        test_student: Student,
        different_user_headers: dict,
        client: AsyncClient,
    ):
        """Test 403 when user doesn't own the student."""
        response = await client.post(
            "/api/v1/learning-plans/generate",
            json={"student_id": test_student.id},
            headers=different_user_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_generate_learning_plan_student_not_found(
        self,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test 404 when student doesn't exist."""
        response = await client.post(
            "/api/v1/learning-plans/generate",
            json={"student_id": "non-existent-id"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestLearningPlansGet:
    """Tests for GET /api/v1/learning-plans/{student_id}."""

    @pytest.mark.asyncio
    async def test_get_learning_plan_success(
        self,
        db_session: AsyncSession,
        seed_grade_4_standards,
        test_student: Student,
        test_assessment,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test successful learning plan retrieval."""
        # Seed skill states
        for std in seed_grade_4_standards:
            state = StudentSkillState(
                id=str(uuid4()),
                student_id=test_student.id,
                standard_id=std.id,
                mastery_prob=0.5
            )
            db_session.add(state)
        await db_session.commit()

        # First generate a plan
        gen_response = await client.post(
            "/api/v1/learning-plans/generate",
            json={"student_id": test_student.id, "assessment_id": test_assessment.id},
            headers=auth_headers,
        )
        assert gen_response.status_code == 201

        # Then get it
        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert data["plan"]["student_id"] == test_student.id

    @pytest.mark.asyncio
    async def test_get_learning_plan_not_found(
        self,
        test_student: Student,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test 404 when no plan exists."""
        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.skip(
        reason="client fixture installs a default verify_jwt override, so "
               "requests without Authorization headers cannot reach an "
               "unauthenticated state. Needs a separate unauthed_client."
    )
    @pytest.mark.asyncio
    async def test_get_learning_plan_unauthorized(
        self,
        test_student: Student,
        client: AsyncClient,
    ):
        """Test 401 when not authenticated."""
        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_learning_plan_permission_denied(
        self,
        test_student: Student,
        different_user_headers: dict,
        client: AsyncClient,
    ):
        """Test 403 when user doesn't own the student."""
        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}",
            headers=different_user_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_learning_plan_no_plan_exists(
        self,
        test_student: Student,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test 404 when no active plan exists for student."""
        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestLearningPlansNextLesson:
    """Tests for GET /api/v1/learning-plans/{student_id}/next-lesson."""

    @pytest.mark.asyncio
    async def test_get_next_lesson_success(
        self,
        db_session: AsyncSession,
        seed_grade_4_standards,
        test_student: Student,
        test_assessment,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test successful retrieval of next lesson."""
        # Seed skill states
        for std in seed_grade_4_standards:
            state = StudentSkillState(
                id=str(uuid4()),
                student_id=test_student.id,
                standard_id=std.id,
                mastery_prob=0.5
            )
            db_session.add(state)
        await db_session.commit()

        # Generate plan
        await client.post(
            "/api/v1/learning-plans/generate",
            json={"student_id": test_student.id, "assessment_id": test_assessment.id},
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}/next-lesson",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "module" in data
        assert "lesson" in data

    @pytest.mark.asyncio
    async def test_get_next_lesson_no_available(
        self,
        test_student: Student,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test 404 when no lessons are available."""
        # No plan generated yet
        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}/next-lesson",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_next_lesson_permission_denied(
        self,
        test_student: Student,
        different_user_headers: dict,
        client: AsyncClient,
    ):
        """Test 403 when user doesn't own the student."""
        response = await client.get(
            f"/api/v1/learning-plans/{test_student.id}/next-lesson",
            headers=different_user_headers,
        )

        assert response.status_code == 403


class TestSkillGraphSequence:
    """Tests for GET /api/v1/learning-plans/sequence."""

    @pytest.mark.asyncio
    async def test_get_skill_sequence_success(
        self,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test successful skill sequence retrieval."""
        response = await client.get(
            "/api/v1/learning-plans/sequence?standard_codes=4.NBT.A.1,4.OA.A.1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "sequence" in data
        assert len(data["sequence"]) >= 2

    @pytest.mark.asyncio
    async def test_get_skill_sequence_invalid_graph(
        self,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test sequence retrieval when graph is not loaded."""
        # Patch where it's USED, not where it's defined
        with patch("src.api.v1.endpoints.learning_plans.get_cached_graph", return_value=None):
            response = await client.get(
                "/api/v1/learning-plans/sequence?standard_codes=4.NBT.A.1",
                headers=auth_headers,
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_skill_sequence_empty_codes(
        self,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test sequence retrieval with empty codes."""
        response = await client.get(
            "/api/v1/learning-plans/sequence?standard_codes=",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["length"] == 0


class TestCompleteModuleEndpoint:
    """Tests for POST /api/v1/learning-plans/{plan_id}/modules/{module_id}/complete."""

    @pytest.mark.asyncio
    async def test_complete_module_success(
        self,
        db_session: AsyncSession,
        seed_grade_4_standards,
        test_student: Student,
        test_assessment,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test successful module completion."""
        # Create a plan and module manually
        plan = LearningPlan(
            id="test-plan-123",
            student_id=test_student.id,
            assessment_id=test_assessment.id,
            track="on_track",
            status="active",
            total_modules=1,
            total_lessons=1,
            estimated_total_minutes=20,
            sessions_per_week=3,
            minutes_per_session=20,
            estimated_completion_date=date.today() + timedelta(days=7)
        )
        module = PlanModule(
            id="test-mod-123",
            plan_id=plan.id,
            standard_id="4.NBT.A.1",
            sequence_order=1,
            status="available",
            lesson_count=1,
            estimated_minutes=20
        )
        db_session.add_all([plan, module])
        await db_session.commit()

        response = await client.post(
            f"/api/v1/learning-plans/{plan.id}/modules/{module.id}/complete",
            json={"p_mastered": 0.85, "lessons_completed": 1, "minutes_spent": 20},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_complete_module_invalid_p_mastered(
        self,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test 422 for invalid p_mastered value."""
        response = await client.post(
            "/api/v1/learning-plans/plan-id/modules/module-id/complete",
            json={"p_mastered": 1.5},
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_complete_module_plan_not_found(
        self,
        auth_headers: dict,
        client: AsyncClient,
    ):
        """Test 404 for non-existent plan."""
        response = await client.post(
            "/api/v1/learning-plans/non-existent/modules/module-id/complete",
            json={"p_mastered": 0.85},
            headers=auth_headers,
        )

        assert response.status_code == 404
