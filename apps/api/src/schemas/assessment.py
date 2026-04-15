"""
Pydantic schemas for Assessment model and related entities.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class AssessmentStartRequest(BaseModel):
    """Schema for starting a new assessment."""

    student_id: str
    assessment_type: str = "diagnostic"


class AssessmentStartResponse(BaseModel):
    """Response for starting an assessment."""

    assessment_id: str
    session_id: str
    student_id: str
    assessment_type: str
    target_question_count: int = 35
    status: str = "in_progress"
    started_at: datetime


class QuestionPresentation(BaseModel):
    """Presentation of a question for the student."""

    question_id: str
    question_number: int
    standard_domain: str  # Human-readable domain name
    stem: str
    stem_image_url: Optional[str] = None
    options: List["OptionPresentation"]
    question_type: str


class OptionPresentation(BaseModel):
    """Presentation of a multiple choice option."""

    key: str  # A, B, C, D
    text: str
    image_url: Optional[str] = None


class AssessmentProgress(BaseModel):
    """Progress information for the current assessment."""

    questions_answered: int
    target_total: int
    domains_covered: dict[str, int]  # e.g., {"4.OA": 5, "4.NBT": 3}
    estimated_time_remaining_min: int


class NextQuestionResponse(BaseModel):
    """Response for requesting the next question."""

    question: Optional[QuestionPresentation] = None
    progress: AssessmentProgress
    should_end: bool = False
    end_reason: Optional[str] = None  # all_standards_covered, max_questions_reached


class ResponseSubmission(BaseModel):
    """Schema for submitting a question response."""

    question_id: str
    selected_answer: str = Field(..., pattern=r"^[A-D]$|^\d+(\.\d+)?$")
    time_spent_ms: int = Field(..., ge=0, le=600000)  # Max 10 minutes
    client_timestamp: datetime


class ResponseSubmissionResponse(BaseModel):
    """Response after submitting a question."""

    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    progress: AssessmentProgress


class CompleteAssessmentRequest(BaseModel):
    """Schema for completing an assessment."""

    pass


class CompleteAssessmentResponse(BaseModel):
    """Response after completing an assessment."""

    assessment_id: str
    status: str = "completed"
    total_questions: int
    total_correct: int
    overall_score: float
    duration_minutes: float
    completed_at: datetime
    results_url: str


class DomainResult(BaseModel):
    """Result breakdown by domain."""

    domain_code: str  # e.g., "4.OA"
    domain_name: str  # e.g., "Operations & Algebraic Thinking"
    questions_count: int
    correct_count: int
    score: float
    classification: str  # below_par, on_par, above_par


class SkillStateResult(BaseModel):
    """Individual skill state result."""

    standard_code: str
    standard_title: str
    p_mastery: float
    mastery_level: str  # low, medium, high
    questions_attempted: int
    questions_correct: int


class GapAnalysis(BaseModel):
    """Gap analysis summary."""

    strengths: List[str]  # Standard codes where P(mastery) >= 0.80
    on_track: List[str]   # 0.60 <= P(mastery) < 0.80
    needs_work: List[str] # P(mastery) < 0.60
    recommended_focus_order: List[str]  # Prioritized by impact


class AssessmentResultsResponse(BaseModel):
    """Complete assessment results."""

    assessment_id: str
    student_name: str
    assessment_type: str
    completed_at: datetime
    duration_minutes: float
    overall_score: float
    total_questions: int
    total_correct: int
    overall_classification: str  # below_par, on_par, above_par
    domain_results: List[DomainResult]
    skill_states: List[SkillStateResult]
    gap_analysis: GapAnalysis
