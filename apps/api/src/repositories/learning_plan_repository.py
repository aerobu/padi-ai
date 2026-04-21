"""
Learning Plan Repository for managing learning plans.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import LearningPlan, PlanModule


class LearningPlanRepository:
    """Repository for learning plans."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, plan_id: str) -> Optional[LearningPlan]:
        """Get a learning plan by ID."""
        result = await self.session.execute(
            select(LearningPlan).where(LearningPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_by_student(
        self,
        student_id: str,
        status: Optional[str] = None,
    ) -> Optional[LearningPlan]:
        """Get a student's active learning plan."""
        query = select(LearningPlan).where(LearningPlan.student_id == student_id)

        if status:
            query = query.where(LearningPlan.status == status)

        query = query.order_by(LearningPlan.created_at.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[LearningPlan]:
        """Get all learning plans with optional filters."""
        query = select(LearningPlan).order_by(LearningPlan.created_at.desc())

        if student_id:
            query = query.where(LearningPlan.student_id == student_id)

        if status:
            query = query.where(LearningPlan.status == status)

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, data: dict) -> LearningPlan:
        """Create a new learning plan."""
        plan = LearningPlan(**data)
        self.session.add(plan)
        await self.session.flush()
        await self.session.refresh(plan)
        return plan

    async def update(
        self,
        plan_id: str,
        updates: dict,
    ) -> Optional[LearningPlan]:
        """Update a learning plan."""
        result = await self.session.execute(
            select(LearningPlan).where(LearningPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if plan:
            for key, value in updates.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)
            await self.session.commit()
            await self.session.refresh(plan)

        return plan

    async def get_modules(self, plan_id: str) -> List[PlanModule]:
        """Get all modules for a learning plan."""
        result = await self.session.execute(
            select(PlanModule)
            .where(PlanModule.plan_id == plan_id)
            .order_by(PlanModule.sequence_order)
        )
        return result.scalars().all()
