"""Pydantic schemas for Generation Job endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Generation job status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationJobCreateRequest(BaseModel):
    """Request schema for creating a generation job."""

    standard_code: str = Field(..., min_length=1, description="Standard code")
    requested_count: int = Field(..., ge=1, le=100, description="Number of questions to generate")
    difficulty_levels: Optional[List[int]] = Field(
        default=[1, 2, 3, 4, 5],
        min_length=1,
        max_length=5,
        description="Difficulty levels (1-5)"
    )
    context_themes: Optional[List[str]] = Field(
        default=None,
        min_length=1,
        description="Context themes for questions"
    )


class GenerationJobResponse(BaseModel):
    """Response schema for a generation job."""

    job_id: str
    standard_code: str
    requested_count: int
    status: str
    created_at: Optional[datetime] = None


class GenerationJobListResponse(BaseModel):
    """Response schema for listing generation jobs."""

    jobs: List[dict]
    total: int
    limit: int
    offset: int


class GenerationJobDetailResponse(BaseModel):
    """Response schema for generation job details."""

    job: dict
    questions: List[dict]


class ExecuteJobResponse(BaseModel):
    """Response schema for executing a job."""

    job_id: str
    status: str
    total_generated: int
    auto_approved: int
    needs_review: int
    completed_at: Optional[datetime] = None


class ReviewQueueItem(BaseModel):
    """Response schema for review queue item."""

    id: str
    generated_question_id: str
    priority: int
    confidence_score: float
    flags: Optional[dict] = None
    created_at: Optional[datetime] = None


class ReviewQueueResponse(BaseModel):
    """Response schema for review queue endpoint."""

    review_queue: List[ReviewQueueItem]
    total: int
