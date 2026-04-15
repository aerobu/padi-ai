"""
Student repository with consent validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AsyncRepository
from src.models.models import Student, ConsentRecord, ConsentStatus


class StudentRepository(AsyncRepository[Student]):
    """Repository for Student model with consent-aware operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Student)

    async def get_by_parent_id(self, parent_id: str) -> List[Student]:
        """Get all students for a parent."""
        result = await self.session.execute(
            select(Student).where(Student.parent_id == parent_id)
        )
        return list(result.scalars().all())

    async def create_with_consent_check(
        self, data: Dict[str, Any], parent_id: str, has_active_consent: bool
    ) -> Student:
        """Create a student, but only if parent has active consent."""
        if not has_active_consent:
            raise ValueError("Active COPPA consent required to create student")

        data["parent_id"] = parent_id
        return await self.create(data)

    async def get_with_latest_assessment(self, student_id: str) -> Optional[Student]:
        """Get student with latest assessment info."""
        from src.models.models import Assessment

        result = await self.session.execute(
            select(Student)
            .where(Student.id == student_id)
            .options(selectinload(Student.assessments))
        )
        student = result.scalar_one_or_none()

        if student and student.assessments:
            # Sort by created_at descending and get latest
            student.assessments.sort(
                key=lambda a: a.created_at or datetime.min, reverse=True
            )
            student.latest_assessment = student.assessments[0]
        else:
            student.latest_assessment = None

        return student

    async def update_skill_summary(self, student_id: str) -> Dict[str, int]:
        """Update skill summary for student."""
        from src.models.models import StudentSkillState

        result = await self.session.execute(
            select(StudentSkillState).where(StudentSkillState.student_id == student_id)
        )
        skill_states = result.scalars().all()

        summary = {
            "total_standards": len(skill_states),
            "mastered": 0,  # p_mastery >= 0.80
            "on_par": 0,    # 0.60 <= p_mastery < 0.80
            "below_par": 0, # p_mastery < 0.60
            "not_assessed": 0,
        }

        for state in skill_states:
            if state.p_mastery >= 0.80:
                summary["mastered"] += 1
            elif state.p_mastery >= 0.60:
                summary["on_par"] += 1
            else:
                summary["below_par"] += 1

        return summary

    async def delete(self, id: str) -> bool:
        """Delete a student (cascades to related records)."""
        result = await self.session.execute(
            self.session.delete(self.model(id=id))
        )
        await self.session.commit()
        return result.rowcount > 0
