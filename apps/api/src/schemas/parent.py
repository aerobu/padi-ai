"""
Pydantic schemas for parent dashboard endpoints.
"""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Track(str, Enum):
    """Learning plan track classifications."""

    CATCH_UP = "catch_up"
    ON_TRACK = "on_track"
    ACCELERATE = "accelerate"


class ChildSummaryResponse(BaseModel):
    """Summary of a child's progress for parent dashboard."""

    child_id: str
    name: str
    grade: int
    track: Optional[Track] = None
    plan_start: Optional[date] = None
    estimated_completion: Optional[date] = None
    overall_progress: float = 0.0
    modules_completed: int = 0
    total_modules: int = 0


class ParentDashboardResponse(BaseModel):
    """Parent dashboard response with all children summaries."""

    children: List[ChildSummaryResponse]


class NotificationFrequency(str, Enum):
    """Notification frequency options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


class NotificationPreferences(BaseModel):
    """Notification preferences for a parent."""

    email_weekly_summary: bool = True
    email_milestone_achievements: bool = True
    sms_reminders: bool = False
    notification_frequency: NotificationFrequency = NotificationFrequency.WEEKLY


class DetailedReportResponse(BaseModel):
    """Detailed progress report for all children."""

    children: List[dict]
