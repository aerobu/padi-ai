"""
Pydantic schemas for PADI.AI API.
"""

from .response import ApiResponse
from .user import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDetailResponse,
    ConsentInitiateRequest,
    ConsentInitiateResponse,
    ConsentConfirmRequest,
    ConsentConfirmResponse,
    ConsentStatusResponse,
    ConsentRecordSummary,
)
from .assessment import (
    AssessmentStartRequest,
    AssessmentStartResponse,
    QuestionPresentation,
    OptionPresentation,
    AssessmentProgress,
    NextQuestionResponse,
    ResponseSubmission,
    ResponseSubmissionResponse,
    CompleteAssessmentResponse,
    DomainResult,
    SkillStateResult,
    GapAnalysis,
    AssessmentResultsResponse,
)
from .standard import (
    StandardQueryParams,
    StandardListItem,
    StandardListResponse,
    StandardDetailResponse,
)

__all__ = [
    # Response
    "ApiResponse",
    # User
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentDetailResponse",
    "ConsentInitiateRequest",
    "ConsentInitiateResponse",
    "ConsentConfirmRequest",
    "ConsentConfirmResponse",
    "ConsentStatusResponse",
    "ConsentRecordSummary",
    # Assessment
    "AssessmentStartRequest",
    "AssessmentStartResponse",
    "QuestionPresentation",
    "OptionPresentation",
    "AssessmentProgress",
    "NextQuestionResponse",
    "ResponseSubmission",
    "ResponseSubmissionResponse",
    "CompleteAssessmentResponse",
    "DomainResult",
    "SkillStateResult",
    "GapAnalysis",
    "AssessmentResultsResponse",
    # Standard
    "StandardQueryParams",
    "StandardListItem",
    "StandardListResponse",
    "StandardDetailResponse",
]
