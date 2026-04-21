"""
Streak Service for activity tracking.
Handles daily activity recording and streak management.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import StudentStreak, PracticeSession


class StreakService:
    """Service for managing student activity streaks."""

    # Pacific Time offset (UTC-8 standard, UTC-7 during DST)
    PACIFIC_OFFSET = timedelta(hours=-8)
    PACIFIC_TZ = timezone(PACIFIC_OFFSET)

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def record_activity(
        self,
        student_id: str,
        practice_session_id: str,
    ) -> int:
        """
        Record that a student completed a practice session today.

        Args:
            student_id: Student ID
            practice_session_id: Practice session ID

        Returns:
            Current streak count after recording
        """
        # Get or create student streak record
        streak = await self._get_or_create_streak(student_id)

        # Get today's date in Pacific Time
        today = datetime.now(self.PACIFIC_TZ).date()

        # Convert activity_dates list to set for easier manipulation
        activity_set = set(streak.activity_dates) if streak.activity_dates else set()

        # Check if already recorded for today
        if today in activity_set:
            return streak.current_streak_days

        # Check if yesterday's activity exists (to continue streak)
        yesterday = today - timedelta(days=1)
        prev_activity = streak.last_activity_date if streak.last_activity_date else None

        if prev_activity == yesterday:
            # Continue the streak
            new_streak = streak.current_streak_days + 1
        else:
            # Start new streak or reset
            new_streak = 1
            # Update longest streak if needed
            if streak.current_streak_days > streak.longest_streak_days:
                streak.longest_streak_days = streak.current_streak_days

        # Update streak
        streak.current_streak_days = new_streak
        streak.last_activity_date = today
        streak.activity_dates.append(today)

        # Update weekly/monthly counts
        await self._update_counts(streak, today)

        # Update total sessions
        streak.total_practice_sessions += 1

        return new_streak

    async def _get_or_create_streak(self, student_id: str) -> StudentStreak:
        """Get existing streak or create new one."""
        result = await self.db_session.execute(
            select(StudentStreak).where(StudentStreak.student_id == student_id)
        )
        streak = result.scalars().first()

        if not streak:
            streak = StudentStreak(
                id=str(__import__('uuid').uuid4()),
                student_id=student_id,
                current_streak_days=0,
                longest_streak_days=0,
                last_activity_date=None,
                activity_dates=[],
                activities_this_week=0,
                activities_this_month=0,
                total_practice_sessions=0,
                total_questions_answered=0,
                total_time_spent_minutes=0,
            )
            self.db_session.add(streak)
            await self.db_session.flush()

        return streak

    async def _update_counts(
        self,
        streak: StudentStreak,
        today: date,
    ) -> None:
        """Update weekly and monthly activity counts."""
        activity_set = set(streak.activity_dates) if streak.activity_dates else set()

        # Calculate week start (Monday)
        week_start = today - timedelta(days=today.weekday())

        # Calculate month start
        month_start = today.replace(day=1)

        # Count activities this week
        week_count = sum(1 for d in activity_set if d >= week_start)

        # Count activities this month
        month_count = sum(1 for d in activity_set if d >= month_start)

        streak.activities_this_week = week_count
        streak.activities_this_month = month_count

    async def get_streak_info(self, student_id: str) -> dict:
        """
        Get current streak info for display.

        Returns:
            Dictionary with streak stats and heatmap
        """
        result = await self.db_session.execute(
            select(StudentStreak).where(StudentStreak.student_id == student_id)
        )
        streak = result.scalars().first()

        if not streak:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "activity_heatmap": [],
                "activities_this_week": 0,
                "activities_this_month": 0,
            }

        # Generate 90-day activity heatmap
        today = datetime.now(self.PACIFIC_TZ).date()
        heatmap = []

        for i in range(90):
            day = today - timedelta(days=i)
            activity_count = 1 if day in (set(streak.activity_dates) if streak.activity_dates else set()) else 0
            heatmap.append({
                "date": day.isoformat(),
                "count": activity_count,
            })

        return {
            "current_streak": streak.current_streak_days,
            "longest_streak": streak.longest_streak_days,
            "last_activity_date": streak.last_activity_date.isoformat() if streak.last_activity_date else None,
            "activities_this_week": streak.activities_this_week,
            "activities_this_month": streak.activities_this_month,
            "total_practice_sessions": streak.total_practice_sessions,
            "activity_heatmap": heatmap,
        }

    async def get_weekly_goal_progress(
        self,
        student_id: str,
        goal_minutes: int = 100,
    ) -> dict:
        """
        Get weekly practice goal progress.

        Args:
            student_id: Student ID
            goal_minutes: Weekly goal in minutes (default 100)

        Returns:
            Progress dictionary with current progress and goal
        """
        streak_result = await self.db_session.execute(
            select(StudentStreak).where(StudentStreak.student_id == student_id)
        )
        streak = streak_result.scalars().first()

        if not streak:
            return {
                "current_minutes": 0,
                "goal_minutes": goal_minutes,
                "progress_percent": 0,
                "on_track": True,
            }

        # Get sessions for this week
        today = datetime.now(self.PACIFIC_TZ).date()
        week_start = today - timedelta(days=today.weekday())

        sessions_result = await self.db_session.execute(
            select(PracticeSession)
            .where(
                PracticeSession.student_id == student_id,
                PracticeSession.created_at >= week_start,
                PracticeSession.status == "completed",
            )
        )
        sessions = sessions_result.scalars().all()

        total_minutes = sum(
            s.actual_minutes if s.actual_minutes else 0
            for s in sessions
        )

        progress_percent = min(100, (total_minutes / goal_minutes) * 100)
        on_track = progress_percent >= 70  # On track if 70%+

        return {
            "current_minutes": total_minutes,
            "goal_minutes": goal_minutes,
            "progress_percent": progress_percent,
            "on_track": on_track,
            "sessions_completed": len(sessions),
        }
