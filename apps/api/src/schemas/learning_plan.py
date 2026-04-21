"""Pydantic schemas for Learning Plan endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LearningPlanGenerateRequest(BaseModel):
    """Request schema for generating a learning plan."""

    student_id: str = Field(..., min_length=1, description="Student ID")
    assessment_id: Optional[str] = Field(None, min_length=1, description="Optional assessment ID")


class ModuleCompleteRequest(BaseModel):
    """Request schema for completing a module."""

    p_mastered: float = Field(..., ge=0.0, le=1.0, description="Mastery probability (0.0-1.0)")
    lessons_completed: int = Field(default=1, ge=0, description="Number of lessons completed")
    minutes_spent: int = Field(default=20, ge=0, description="Minutes spent on module")


class LearningPlanResponse(BaseModel):
    """Response schema for learning plan."""

    plan_id: str
    student_id: str
    track: str
    status: str
    total_modules: int
    completed_modules: int
    total_lessons: int
    completed_lessons: int
    estimated_total_minutes: int
    estimated_completion_date: Optional[datetime] = None
    created_at: datetime


class ModuleResponse(BaseModel):
    """Response schema for a module."""

    id: str
    standard_code: str
    sequence_order: int
    status: str
    lesson_count: int
    completed_lessons: int
    estimated_minutes: int
    entry_p_mastery: float
    exit_p_mastery: float


class LessonResponse(BaseModel):
    """Response schema for a lesson."""

    id: str
    sequence_order: int
    lesson_type: str
    title: str
    status: str
    question_count: int


class LearningPlanWithModulesResponse(BaseModel):
    """Response schema for learning plan with modules and lessons."""

    plan: LearningPlanResponse
    modules: List[ModuleResponse]


class NextLessonResponse(BaseModel):
    """Response schema for next lesson endpoint."""

    module: dict
    lesson: dict


class SkillSequenceResponse(BaseModel):
    """Response schema for skill sequence endpoint."""

    standard_codes: List[str]
    sequence: List[str]
    length: int


class ResponseSubmission(BaseModel):
    """Request schema for submitting an answer in a practice session."""

    answer: str = Field(..., min_length=1, description="Student's answer")
    time_spent_ms: int = Field(default=0, ge=0, description="Time spent in milliseconds")


class SessionAnswerResponse(BaseModel):
    """Response schema for session answer endpoint."""

    correct: bool = Field(..., description="Whether the answer is correct")
    correct_answer: str = Field(..., description="The correct answer")
    explanation: Optional[str] = Field(None, description="Explanation for the answer")
    progress: dict = Field(..., description="Current progress in session")
