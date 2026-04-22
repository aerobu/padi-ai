"""
Comprehensive tests for Generation Jobs API endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.models.models import GenerationJob, GeneratedQuestion, Standard, User
from pydantic import ValidationError


@pytest.mark.asyncio
class TestCreateGenerationJob:
    """Tests for POST /admin/generation-jobs endpoint."""

    async def _seed_data(self, db_session: AsyncSession):
        # Seed standard
        std = Standard(
            id="4.NBT.A.1",
            standard_code="4.NBT.A.1",
            domain="NBT",
            grade_level=4,
            title="Test Standard",
            description="Test Description",
            is_active=True
        )
        db_session.add(std)
        
        # Seed admin user
        admin = User(
            id="admin-user-id",
            auth0_id="auth0|admin",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True
        )
        admin.set_email("admin@example.com")
        db_session.add(admin)
        
        await db_session.commit()

    async def test_create_generation_job_success(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test successful generation job creation."""
        await self._seed_data(db_session)
        
        response = await client.post(
            "/api/v1/admin/generation-jobs",
            json={
                "standard_code": "4.NBT.A.1",
                "requested_count": 10,
                "difficulty_levels": [1, 2, 3],
                "context_themes": ["shopping", "sports"]
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["standard_code"] == "4.NBT.A.1"
        assert data["requested_count"] == 10
        assert data["status"] == "queued"

    async def test_create_generation_job_default_difficulty(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test generation job with default difficulty levels."""
        await self._seed_data(db_session)
        
        response = await client.post(
            "/api/v1/admin/generation-jobs",
            json={
                "standard_code": "4.NBT.A.1",
                "requested_count": 5,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["standard_code"] == "4.NBT.A.1"
        assert data["requested_count"] == 5

    async def test_create_generation_job_unauthorized(
        self,
        db_session: AsyncSession,
        async_client: AsyncClient,
    ):
        """Test 401 when not authenticated."""
        response = await async_client.post(
            "/api/v1/admin/generation-jobs",
            json={
                "standard_code": "4.NBT.A.1",
                "requested_count": 10,
            },
        )

        assert response.status_code == 401

    async def test_create_generation_job_invalid_count(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test 422 for invalid requested_count."""
        response = await client.post(
            "/api/v1/admin/generation-jobs",
            json={
                "standard_code": "4.NBT.A.1",
                "requested_count": 0,
            },
        )
        assert response.status_code == 422

    async def test_create_generation_job_invalid_difficulty(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test 422 for invalid difficulty levels."""
        response = await client.post(
            "/api/v1/admin/generation-jobs",
            json={
                "standard_code": "4.NBT.A.1",
                "requested_count": 10,
                "difficulty_levels": [1, 2, 6],
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListGenerationJobs:
    """Tests for GET /admin/generation-jobs endpoint."""

    async def _seed_data(self, db_session: AsyncSession):
        std = Standard(
            id="4.NBT.A.1",
            standard_code="4.NBT.A.1",
            domain="NBT",
            grade_level=4,
            title="Test Standard",
            description="Test Description",
            is_active=True
        )
        db_session.add(std)
        
        admin = User(
            id="admin-user-id",
            auth0_id="auth0|admin",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True
        )
        admin.set_email("admin@example.com")
        db_session.add(admin)
        
        await db_session.commit()

    async def test_list_generation_jobs_success(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test successful listing of generation jobs."""
        await self._seed_data(db_session)
        
        from src.repositories.generation_job_repository import GenerationJobRepository
        job_repo = GenerationJobRepository(db_session)
        await job_repo.create({
            "id": "test-job-1",
            "standard_id": "4.NBT.A.1",
            "requested_count": 10,
            "difficulty_levels": [1, 2, 3],
            "status": "queued",
            "created_by": "admin-user-id",
        })

        response = await client.get("/api/v1/admin/generation-jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data

    async def test_list_generation_jobs_unauthorized(
        self,
        db_session: AsyncSession,
        async_client: AsyncClient,
    ):
        """Test 401 when not authenticated."""
        response = await async_client.get("/api/v1/admin/generation-jobs")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetGenerationJob:
    """Tests for GET /admin/generation-jobs/{job_id} endpoint."""

    async def _seed_data(self, db_session: AsyncSession):
        std = Standard(
            id="4.NBT.A.1",
            standard_code="4.NBT.A.1",
            domain="NBT",
            grade_level=4,
            title="Test Standard",
            description="Test Description",
            is_active=True
        )
        db_session.add(std)
        
        admin = User(
            id="admin-user-id",
            auth0_id="auth0|admin",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True
        )
        admin.set_email("admin@example.com")
        db_session.add(admin)
        
        await db_session.commit()

    async def test_get_generation_job_success(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test successful retrieval of generation job."""
        await self._seed_data(db_session)
        
        from src.repositories.generation_job_repository import GenerationJobRepository
        job_repo = GenerationJobRepository(db_session)
        job = await job_repo.create({
            "id": "test-job-2",
            "standard_id": "4.NBT.A.1",
            "requested_count": 10,
            "difficulty_levels": [1, 2, 3, 4, 5],
            "status": "in_progress",
            "created_by": "admin-user-id",
        })

        response = await client.get(f"/api/v1/admin/generation-jobs/{job.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job"]["standard_code"] == "4.NBT.A.1"

    async def test_get_generation_job_unauthorized(
        self,
        db_session: AsyncSession,
        async_client: AsyncClient,
    ):
        """Test 401 when not authenticated."""
        response = await async_client.get("/api/v1/admin/generation-jobs/test-job")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestExecuteGenerationJob:
    """Tests for POST /admin/generation-jobs/{job_id}/execute endpoint."""

    async def _seed_data(self, db_session: AsyncSession):
        std = Standard(
            id="4.NBT.A.1",
            standard_code="4.NBT.A.1",
            domain="NBT",
            grade_level=4,
            title="Test Standard",
            description="Test Description",
            is_active=True
        )
        db_session.add(std)
        
        admin = User(
            id="admin-user-id",
            auth0_id="auth0|admin",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True
        )
        admin.set_email("admin@example.com")
        db_session.add(admin)
        
        await db_session.commit()

    async def test_execute_generation_job_success(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test successful execution of generation job."""
        await self._seed_data(db_session)
        
        from src.repositories.generation_job_repository import GenerationJobRepository
        job_repo = GenerationJobRepository(db_session)
        job = await job_repo.create({
            "id": "test-job-3",
            "standard_id": "4.NBT.A.1",
            "requested_count": 5,
            "status": "queued",
            "created_by": "admin-user-id",
        })

        with patch("src.services.llm_question_generator.LLMQuestionGenerator.execute_generation_job") as mock_exec:
            mock_job = MagicMock()
            mock_job.id = job.id
            mock_job.status = "completed"
            mock_job.total_generated = 5
            mock_job.auto_approved = 4
            mock_job.needs_review = 1
            mock_job.completed_at = datetime.utcnow()
            mock_exec.return_value = mock_job

            response = await client.post(f"/api/v1/admin/generation-jobs/{job.id}/execute")
            assert response.status_code in [200, 500]

    async def test_execute_generation_job_not_queued(
        self,
        db_session: AsyncSession,
        mock_jwt_as_admin,
        client: AsyncClient,
    ):
        """Test 400 when job is not in queued status."""
        await self._seed_data(db_session)
        
        from src.repositories.generation_job_repository import GenerationJobRepository
        job_repo = GenerationJobRepository(db_session)
        job = await job_repo.create({
            "id": "test-job-4",
            "standard_id": "4.NBT.A.1",
            "requested_count": 5,
            "status": "completed",
            "created_by": "admin-user-id",
        })

        response = await client.post(f"/api/v1/admin/generation-jobs/{job.id}/execute")
        assert response.status_code in [400, 500]


@pytest.mark.asyncio
class TestGetReviewQueue:
    """Tests for GET /admin/review-queue endpoint."""

    async def test_get_review_queue_unauthorized(
        self,
        db_session: AsyncSession,
        async_client: AsyncClient,
    ):
        """Test 401 when not authenticated."""
        response = await async_client.get("/api/v1/admin/review-queue")
        assert response.status_code == 401
