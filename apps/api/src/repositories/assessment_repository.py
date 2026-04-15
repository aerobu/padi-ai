"""
Assessment repository for session and response management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AsyncRepository
from src.models.models import (
    Assessment,
    AssessmentSession,
    AssessmentResponse,
    AssessmentStatus,
)


class AssessmentRepository(AsyncRepository[Assessment]):
    """Repository for Assessment model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Assessment)

    async def get_by_student_id(self, student_id: str) -> List[Assessment]:
        """Get all assessments for a student."""
        result = await self.session.execute(
            select(Assessment).where(Assessment.student_id == student_id)
        )
        return list(result.scalars().all())

    async def get_active_diagnostic(
        self, student_id: str
    ) -> Optional[Assessment]:
        """Get active diagnostic assessment for student."""
        result = await self.session.execute(
            select(Assessment)
            .where(
                Assessment.student_id == student_id,
                Assessment.assessment_type == "diagnostic",
                Assessment.status == AssessmentStatus.IN_PROGRESS,
            )
            .order_by(Assessment.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def create_session(
        self, assessment_id: str, student_id: str
    ) -> AssessmentSession:
        """Create a new assessment session."""
        session = AssessmentSession(
            assessment_id=assessment_id,
            student_id=student_id,
            started_at=datetime.utcnow(),
            status="in_progress",
        )
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[AssessmentSession]:
        """Get assessment session by ID."""
        result = await self.session.execute(
            select(AssessmentSession).where(AssessmentSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def complete_session(
        self, session_id: str, completed_at: datetime
    ) -> Optional[AssessmentSession]:
        """Mark session as completed."""
        statement = (
            AssessmentSession.__table__.update()
            .where(AssessmentSession.id == session_id)
            .values(status="completed", completed_at=completed_at)
        )
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_session(session_id)

    async def record_response(
        self,
        session_id: str,
        question_id: str,
        student_answer: str,
        is_correct: bool,
        points_earned: float,
        time_spent_seconds: int,
        hint_count: int = 0,
    ) -> AssessmentResponse:
        """Record a student response."""
        response = AssessmentResponse(
            assessment_session_id=session_id,
            question_id=question_id,
            student_answer=student_answer,
            is_correct=is_correct,
            points_earned=points_earned,
            time_spent_seconds=time_spent_seconds,
            hint_count=hint_count,
        )
        self.session.add(response)
        await self.session.commit()
        await self.session.refresh(response)
        return response

    async def get_responses_for_session(
        self, session_id: str
    ) -> List[AssessmentResponse]:
        """Get all responses for a session."""
        result = await self.session.execute(
            select(AssessmentResponse)
            .where(AssessmentResponse.assessment_session_id == session_id)
            .order_by(AssessmentResponse.created_at)
        )
        return list(result.scalars().all())

    async def update_assessment_status(
        self, assessment_id: str, status: str, total_score: float = None
    ) -> Optional[Assessment]:
        """Update assessment status."""
        updates = {"status": status}
        if total_score is not None:
            updates["total_score"] = total_score

        statement = (
            select(Assessment)
            .where(Assessment.id == assessment_id)
            .with_for_update()
        )
        result = await self.session.execute(statement)
        assessment = result.scalar_one_or_none()

        if assessment:
            assessment.status = status
            if total_score is not None:
                assessment.total_score = total_score
            await self.session.commit()
            await self.session.refresh(assessment)

        return assessment


class AssessmentSessionRepository(AsyncRepository[AssessmentSession]):
    """Repository for AssessmentSession model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AssessmentSession)

    async def get_active_for_student(self, student_id: str) -> bool:
        """Check if student has an active assessment."""
        result = await self.session.execute(
            select(AssessmentSession.id)
            .where(
                AssessmentSession.student_id == student_id,
                AssessmentSession.status == "in_progress",
            )
        )
        return result.scalar_one_or_none() is not None
