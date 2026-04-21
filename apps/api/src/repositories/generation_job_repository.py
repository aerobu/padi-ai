"""
Generation Job Repository for AI question generation jobs.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import GenerationJob


class GenerationJobRepository:
    """Repository for generation jobs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, job_id: str) -> Optional[GenerationJob]:
        """Get a generation job by ID."""
        result = await self.session.execute(
            select(GenerationJob).where(GenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[GenerationJob]:
        """Get all generation jobs with optional status filter."""
        query = select(GenerationJob).order_by(GenerationJob.created_at.desc())

        if status:
            query = query.where(GenerationJob.status == status)

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_next_queued(self) -> Optional[GenerationJob]:
        """Get the next queued job to process."""
        result = await self.session.execute(
            select(GenerationJob)
            .where(GenerationJob.status == "queued")
            .order_by(GenerationJob.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> GenerationJob:
        """Create a new generation job."""
        job = GenerationJob(**data)
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def update_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[GenerationJob]:
        """Update job status."""
        result = await self.session.execute(
            select(GenerationJob).where(GenerationJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            await self.session.commit()
            await self.session.refresh(job)

        return job
