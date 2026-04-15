"""
Standard repository for Oregon math standards.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AsyncRepository
from src.models.models import Standard


class StandardRepository(AsyncRepository[Standard]):
    """Repository for Standard model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Standard)

    async def get_by_grade(self, grade: int) -> List[Standard]:
        """Get all standards for a grade level."""
        result = await self.session.execute(
            select(Standard)
            .where(Standard.grade_level == grade, Standard.is_active == True)
            .order_by(Standard.domain, Standard.standard_code)
        )
        return list(result.scalars().all())

    async def get_by_domain(self, grade: int, domain: str) -> List[Standard]:
        """Get standards for a specific grade and domain."""
        result = await self.session.execute(
            select(Standard)
            .where(
                Standard.grade_level == grade,
                Standard.domain == domain,
                Standard.is_active == True,
            )
            .order_by(Standard.standard_code)
        )
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Optional[Standard]:
        """Get standard by its code."""
        result = await self.session.execute(
            select(Standard).where(Standard.standard_code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_codes(self, codes: List[str]) -> List[Standard]:
        """Get multiple standards by codes."""
        result = await self.session.execute(
            select(Standard).where(Standard.standard_code.in_(codes))
        )
        return list(result.scalars().all())

    async def get_all_active(self) -> List[Standard]:
        """Get all active standards."""
        result = await self.session.execute(
            select(Standard).where(Standard.is_active == True).order_by(
                Standard.grade_level, Standard.domain, Standard.standard_code
            )
        )
        return list(result.scalars().all())

    async def get_question_count(self, standard_id: str) -> int:
        """Get question count for a standard."""
        from sqlalchemy import func
        from src.models.models import Question

        result = await self.session.execute(
            select(func.count(Question.id))
            .where(Question.standard_id == standard_id, Question.is_active == True)
        )
        return result.scalar_one()

    async def get_prerequisites(self, standard_id: str) -> List[str]:
        """Get prerequisite standard codes for a standard."""
        from src.models.models import PrerequisiteRelationship

        result = await self.session.execute(
            select(PrerequisiteRelationship)
            .where(PrerequisiteRelationship.standard_id == standard_id)
        )
        relationships = result.scalars().all()
        return [r.prerequisite_id for r in relationships]

    async def get_dependents(self, standard_id: str) -> List[str]:
        """Get dependent standard codes (standards that have this as prereq)."""
        from src.models.models import PrerequisiteRelationship

        result = await self.session.execute(
            select(PrerequisiteRelationship)
            .where(PrerequisiteRelationship.prerequisite_id == standard_id)
        )
        relationships = result.scalars().all()
        return [r.standard_id for r in relationships]
