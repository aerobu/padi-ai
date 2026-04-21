"""
Badge Service for gamification.
Handles badge awarding based on student progress and achievements.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import StudentBadge, BadgeTier


class BadgeType(str, Enum):
    """Badge types available for students."""

    FIRST_SESSION = "first_session"
    STREAK_3 = "streak_3"
    STREAK_7 = "streak_7"
    STREAK_30 = "streak_30"
    HALFWAY = "halfway"
    PLAN_COMPLETE = "plan_complete"
    PERFECT_MODULE = "perfect_module"
    SPEED_DEMON = "speed_demon"
    FOCUS = "focus"
    PERFECT_WEEK = "perfect_week"
    MATH_WIZARD = "math_wizard"


# Badge definitions with tier and display info
BADGE_DEFINITIONS = {
    BadgeType.FIRST_SESSION: {
        "tier": BadgeTier.BRONZE,
        "name": "Math Explorer",
        "description": "Completed your first practice session!",
        "icon_url": "/badges/explorer.svg",
    },
    BadgeType.STREAK_3: {
        "tier": BadgeTier.BRONZE,
        "name": "On a Roll!",
        "description": "3-day activity streak!",
        "icon_url": "/badges/roll.svg",
    },
    BadgeType.STREAK_7: {
        "tier": BadgeTier.SILVER,
        "name": "Week Warrior",
        "description": "7-day activity streak!",
        "icon_url": "/badges/warrior.svg",
    },
    BadgeType.STREAK_30: {
        "tier": BadgeTier.GOLD,
        "name": "Month Master",
        "description": "30-day activity streak!",
        "icon_url": "/badges/master.svg",
    },
    BadgeType.HALFWAY: {
        "tier": BadgeTier.SILVER,
        "name": "Halfway Hero",
        "description": "Completed half of your learning plan!",
        "icon_url": "/badges/halfway.svg",
    },
    BadgeType.PLAN_COMPLETE: {
        "tier": BadgeTier.PLATINUM,
        "name": "Grade Ready!",
        "description": "Completed your entire learning plan!",
        "icon_url": "/badges/ready.svg",
    },
    BadgeType.PERFECT_MODULE: {
        "tier": BadgeTier.GOLD,
        "name": "Perfect Score",
        "description": "Mastered a module with 100% accuracy!",
        "icon_url": "/badges/perfect.svg",
    },
    BadgeType.SPEED_DEMON: {
        "tier": BadgeTier.SILVER,
        "name": "Speed Demon",
        "description": "Completed 3 modules in one week!",
        "icon_url": "/badges/speed.svg",
    },
    BadgeType.FOCUS: {
        "tier": BadgeTier.GOLD,
        "name": "Super Focused",
        "description": "10 consecutive correct answers!",
        "icon_url": "/badges/focus.svg",
    },
    BadgeType.PERFECT_WEEK: {
        "tier": BadgeTier.SILVER,
        "name": "Perfect Week",
        "description": "All questions answered correctly this week!",
        "icon_url": "/badges/perfect_week.svg",
    },
    BadgeType.MATH_WIZARD: {
        "tier": BadgeTier.PLATINUM,
        "name": "Math Wizard",
        "description": "Mastered 50+ skills!",
        "icon_url": "/badges/wizard.svg",
    },
}


class BadgeService:
    """Service for badge management and awarding."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def check_and_award_badges(
        self,
        student_id: str,
        activity_type: str,
        **kwargs,
    ) -> list[BadgeType]:
        """
        Check if student has earned new badges.

        Args:
            student_id: Student ID
            activity_type: Type of activity (session_complete, week_complete, etc.)
            **kwargs: Additional context data

        Returns:
            List of newly awarded badge types
        """
        awarded = []

        # Check first session badge
        if activity_type == "first_session":
            if await self._check_first_session(student_id):
                awarded.append(BadgeType.FIRST_SESSION)

        # Check streak badges
        if activity_type == "session_complete":
            streak_badges = await self._check_streak_badges(student_id)
            awarded.extend(streak_badges)

        # Check halfway badge
        if activity_type == "plan_progress":
            if await self._check_halfway(student_id, kwargs.get('modules_completed', 0), kwargs.get('total_modules', 0)):
                awarded.append(BadgeType.HALFWAY)

        # Check plan complete badge
        if activity_type == "plan_complete":
            if await self._check_plan_complete(student_id):
                awarded.append(BadgeType.PLAN_COMPLETE)

        # Check perfect module badge
        if activity_type == "module_complete":
            if await self._check_perfect_module(student_id, kwargs.get('accuracy', 100)):
                awarded.append(BadgeType.PERFECT_MODULE)

        # Check focus badge
        if activity_type == "session_complete":
            if await self._check_focus(student_id, kwargs.get('correct_count', 0), kwargs.get('total_count', 0)):
                awarded.append(BadgeType.FOCUS)

        # Award badges
        for badge_type in awarded:
            await self._award_badge(student_id, badge_type)

        return awarded

    async def _check_first_session(self, student_id: str) -> bool:
        """Check if student has completed their first session."""
        from src.models.models import PracticeSession

        result = await self.db_session.execute(
            select(PracticeSession)
            .where(PracticeSession.student_id == student_id)
            .limit(1)
        )
        sessions = result.scalars().all()
        return len(sessions) == 1  # First session just completed

    async def _check_streak_badges(self, student_id: str) -> list[BadgeType]:
        """Check for streak-based badges."""
        from src.models.models import StudentStreak

        result = await self.db_session.execute(
            select(StudentStreak).where(StudentStreak.student_id == student_id)
        )
        streak = result.scalars().first()

        awarded = []
        current_streak = streak.current_streak_days if streak else 0

        if current_streak >= 30 and not await self._has_badge(student_id, BadgeType.STREAK_30):
            awarded.append(BadgeType.STREAK_30)
        elif current_streak >= 7 and not await self._has_badge(student_id, BadgeType.STREAK_7):
            awarded.append(BadgeType.STREAK_7)
        elif current_streak >= 3 and not await self._has_badge(student_id, BadgeType.STREAK_3):
            awarded.append(BadgeType.STREAK_3)

        return awarded

    async def _check_halfway(
        self,
        student_id: str,
        modules_completed: int,
        total_modules: int,
    ) -> bool:
        """Check if student has completed half of their plan."""
        if total_modules == 0:
            return False
        progress = modules_completed / total_modules
        return progress >= 0.5 and not await self._has_badge(student_id, BadgeType.HALFWAY)

    async def _check_plan_complete(self, student_id: str) -> bool:
        """Check if student has completed their entire plan."""
        from src.models.models import LearningPlan, ModuleStatus

        result = await self.db_session.execute(
            select(LearningPlan)
            .join(LearningPlan.modules)
            .where(
                LearningPlan.student_id == student_id,
                LearningPlan.status == "active",
            )
        )
        plan = result.scalars().first()

        if not plan:
            return False

        # Check if all modules are completed
        completed_count = sum(
            1 for m in plan.modules if m.status == ModuleStatus.COMPLETED.value
        )
        return (
            completed_count == len(plan.modules)
            and len(plan.modules) > 0
            and not await self._has_badge(student_id, BadgeType.PLAN_COMPLETE)
        )

    async def _check_perfect_module(
        self,
        student_id: str,
        accuracy: float,
    ) -> bool:
        """Check if student mastered a module with perfect accuracy."""
        return accuracy == 100 and await self._has_any_recent_badge(student_id)

    async def _check_focus(self, student_id: str, correct_count: int, total_count: int) -> bool:
        """Check if student has 10 consecutive correct answers."""
        return correct_count >= 10 and total_count == correct_count and not await self._has_badge(student_id, BadgeType.FOCUS)

    async def _has_badge(self, student_id: str, badge_type: BadgeType) -> bool:
        """Check if student already has a badge."""
        from src.models.models import StudentBadge

        result = await self.db_session.execute(
            select(StudentBadge)
            .where(
                StudentBadge.student_id == student_id,
                StudentBadge.badge_type == badge_type.value,
            )
        )
        return result.scalars().first() is not None

    async def _has_any_recent_badge(self, student_id: str) -> bool:
        """Check if student has any recent badges."""
        from src.models.models import StudentBadge
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=30)

        result = await self.db_session.execute(
            select(StudentBadge)
            .where(
                StudentBadge.student_id == student_id,
                StudentBadge.earned_at >= cutoff,
            )
        )
        return result.scalars().first() is not None

    async def _award_badge(
        self,
        student_id: str,
        badge_type: BadgeType,
    ) -> StudentBadge:
        """Award a badge to a student."""
        definition = BADGE_DEFINITIONS[badge_type]

        badge = StudentBadge(
            id=str(uuid4()),
            student_id=student_id,
            badge_type=badge_type.value,
            badge_name=definition["name"],
            badge_description=definition["description"],
            badge_icon_url=definition["icon_url"],
            badge_tier=definition["tier"].value,
            earned_context={
                "awarded_at": datetime.utcnow().isoformat(),
            },
            earned_at=datetime.utcnow(),
        )

        self.db_session.add(badge)
        return badge

    async def get_student_badges(self, student_id: str) -> list[dict]:
        """Get all badges for a student."""
        from src.models.models import StudentBadge

        result = await self.db_session.execute(
            select(StudentBadge)
            .where(StudentBadge.student_id == student_id)
            .order_by(StudentBadge.earned_at.desc())
        )
        badges = result.scalars().all()

        return [
            {
                "badge_type": b.badge_type,
                "badge_name": b.badge_name,
                "badge_description": b.badge_description,
                "badge_icon_url": b.badge_icon_url,
                "badge_tier": b.badge_tier,
                "earned_at": b.earned_at.isoformat() if b.earned_at else None,
            }
            for b in badges
        ]
