"""
Parent Dashboard endpoints for viewing children's progress.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import verify_jwt
from src.repositories.student_repository import StudentRepository
from src.models.models import (
    LearningPlan,
    LearningPlanStatus,
    ModuleStatus,
    Student,
    PracticeSession,
    PracticeSessionStatus,
)
from src.schemas.parent import (
    ParentDashboardResponse,
    ChildSummaryResponse,
    DetailedReportResponse,
    NotificationPreferences,
)


def get_user_from_credentials(
    credentials: Annotated[dict, Depends(verify_jwt)],
) -> dict:
    """Get current authenticated user from JWT credentials."""
    return credentials


router = APIRouter()


@router.get(
    "/parents/{user_id}/dashboard",
    summary="Get parent dashboard",
    description="Get dashboard summary for all children under this parent.",
)
async def get_parent_dashboard(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
) -> ParentDashboardResponse:
    """
    Parent dashboard: all children summary.

    Returns aggregated progress data for all students under this parent.
    """
    # Verify ownership
    if user_payload.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other parent's data",
        )

    # Fetch all students for this parent
    student_repo = StudentRepository(db)
    students = await student_repo.get_by_parent_id(user_id)

    children = []
    for student in students:
        # Get active learning plan
        plan_result = await db.execute(
            select(LearningPlan)
            .where(
                LearningPlan.student_id == student.id,
                LearningPlan.status == LearningPlanStatus.ACTIVE,
            )
            .order_by(LearningPlan.created_at.desc())
            .limit(1)
        )
        plan = plan_result.scalar_one_or_none()

        if plan:
            modules_completed = sum(
                1 for m in plan.modules if m.status == ModuleStatus.COMPLETED
            )
            total_modules = len(plan.modules)
            overall_progress = modules_completed / total_modules if total_modules > 0 else 0

            children.append(
                ChildSummaryResponse(
                    child_id=student.id,
                    name=student.display_name,
                    grade=student.grade_level,
                    track=plan.track,
                    plan_start=plan.created_at.date() if plan.created_at else None,
                    estimated_completion=plan.estimated_completion_date.date()
                    if plan.estimated_completion_date
                    else None,
                    overall_progress=round(overall_progress, 3),
                    modules_completed=modules_completed,
                    total_modules=total_modules,
                )
            )
        else:
            children.append(
                ChildSummaryResponse(
                    child_id=student.id,
                    name=student.display_name,
                    grade=student.grade_level,
                    track=None,
                    plan_start=None,
                    estimated_completion=None,
                    overall_progress=0.0,
                    modules_completed=0,
                    total_modules=0,
                )
            )

    return ParentDashboardResponse(children=children)


@router.get(
    "/parents/{user_id}/report",
    summary="Get detailed report",
    description="Get detailed progress report for all children.",
)
async def get_detailed_report(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
) -> DetailedReportResponse:
    """
    Get detailed progress report for all children.

    Includes skill mastery, practice history, and recommendations.
    """
    # Verify ownership
    if user_payload.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other parent's data",
        )

    # Fetch all students for this parent
    student_repo = StudentRepository(db)
    students = await student_repo.get_by_parent_id(user_id)

    children_reports = []
    for student in students:
        # Get active learning plan
        plan_result = await db.execute(
            select(LearningPlan)
            .where(
                LearningPlan.student_id == student.id,
                LearningPlan.status == LearningPlanStatus.ACTIVE,
            )
            .order_by(LearningPlan.created_at.desc())
            .limit(1)
        )
        plan = plan_result.scalar_one_or_none()

        if plan:
            # Get skill mastery levels
            from src.models.models import StudentSkillState

            skill_result = await db.execute(
                select(StudentSkillState)
                .where(StudentSkillState.student_id == student.id)
                .order_by(StudentSkillState.mastery_prob.desc())
            )
            skill_states = skill_result.scalars().all()

            skill_mastery = [
                {
                    "standard_code": ss.standard_id,
                    "mastery_prob": round(ss.mastery_prob, 3),
                    "times_practiced": ss.times_practiced,
                }
                for ss in skill_states
            ]

            # Get recent practice activity (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            sessions_result = await db.execute(
                select(PracticeSession)
                .where(
                    PracticeSession.student_id == student.id,
                    PracticeSession.status == PracticeSessionStatus.COMPLETED.value,
                    PracticeSession.created_at >= thirty_days_ago,
                )
                .order_by(PracticeSession.created_at.desc())
            )
            recent_sessions = sessions_result.scalars().all()

            total_minutes = sum(
                s.actual_minutes or 0 for s in recent_sessions
            )
            total_questions = sum(s.question_count or 0 for s in recent_sessions)

            children_reports.append(
                {
                    "child_id": student.id,
                    "display_name": student.display_name,
                    "grade_level": student.grade_level,
                    "learning_plan": {
                        "track": plan.track,
                        "progress": {
                            "modules_completed": sum(
                                1 for m in plan.modules
                                if m.status == ModuleStatus.COMPLETED
                            ),
                            "total_modules": len(plan.modules),
                        },
                    },
                    "skill_mastery": skill_mastery,
                    "recent_activity": {
                        "sessions_completed": len(recent_sessions),
                        "total_minutes": total_minutes,
                        "total_questions": total_questions,
                    },
                }
            )
        else:
            children_reports.append(
                {
                    "child_id": student.id,
                    "display_name": student.display_name,
                    "grade_level": student.grade_level,
                    "learning_plan": None,
                    "skill_mastery": [],
                    "recent_activity": {
                        "sessions_completed": 0,
                        "total_minutes": 0,
                        "total_questions": 0,
                    },
                }
            )

    return DetailedReportResponse(children=children_reports)


@router.get(
    "/parents/{user_id}/preferences",
    summary="Get notification preferences",
    description="Get notification preferences for a parent.",
)
async def get_notification_preferences(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
) -> NotificationPreferences:
    """Get notification preferences for a parent."""
    # Verify ownership
    if user_payload.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other parent's data",
        )

    # TODO: Store preferences in database
    # For now, return defaults
    return NotificationPreferences(
        email_weekly_summary=True,
        email_milestone_achievements=True,
        sms_reminders=False,
        notification_frequency="weekly",
    )


@router.put(
    "/parents/{user_id}/preferences",
    summary="Update notification preferences",
    description="Update notification preferences for a parent.",
)
async def update_notification_preferences(
    user_id: str,
    request: NotificationPreferences,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
) -> NotificationPreferences:
    """Update notification preferences for a parent."""
    # Verify ownership
    if user_payload.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other parent's data",
        )

    # TODO: Save preferences to database

    return request
