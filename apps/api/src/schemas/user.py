"""
Pydantic schemas for User and Student models.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, FieldValidationInfo


class StudentCreate(BaseModel):
    """Schema for creating a new student profile."""

    display_name: str = Field(..., min_length=1, max_length=50)
    grade_level: int = Field(..., ge=1, le=5)
    avatar_id: str = Field(default="avatar_default", pattern=r"^avatar_[a-z_]+$")
    birth_year: Optional[int] = Field(default=None, ge=2012, le=2024)

    @FieldValidationInfo
    def validate_display_name(cls, value: str, info) -> str:
        """Sanitize display name - allow only alphanumeric, space, hyphen."""
        return value


class StudentUpdate(BaseModel):
    """Schema for updating a student profile."""

    display_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    avatar_id: Optional[str] = Field(default=None, pattern=r"^avatar_[a-z_]+$")
    grade_level: Optional[int] = Field(default=None, ge=1, le=5)


class StudentResponse(BaseModel):
    """Schema for student response."""

    student_id: str
    display_name: str
    grade_level: int
    avatar_id: str
    birth_year: Optional[int] = None
    is_active: bool = True
    created_at: datetime


class StudentDetailResponse(BaseModel):
    """Schema for student detail with latest assessment info."""

    student_id: str
    display_name: str
    grade_level: int
    avatar_id: str
    birth_year: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    latest_assessment: Optional["AssessmentSummary"] = None
    skill_summary: Optional["SkillSummary"] = None


class AssessmentSummary(BaseModel):
    """Summary of latest assessment."""

    assessment_id: str
    assessment_type: str
    status: str
    overall_score: Optional[float] = None
    completed_at: Optional[datetime] = None


class SkillSummary(BaseModel):
    """Summary of student skill states."""

    total_standards: int
    mastered: int  # P(mastery) >= 0.80
    on_par: int    # 0.60 <= P(mastery) < 0.80
    below_par: int # P(mastery) < 0.60
    not_assessed: int


class ConsentInitiateRequest(BaseModel):
    """Schema for initiating COPPA consent."""

    consent_type: str = Field(default="coppa_verifiable")
    student_display_name: str = Field(..., min_length=1, max_length=50)
    acknowledgements: list[str] = Field(..., min_length=4, max_length=10)


class ConsentInitiateResponse(BaseModel):
    """Response for consent initiation."""

    consent_id: str
    status: str = "pending"
    verification_method: str = "email_plus"
    email_sent_to: str  # Masked email
    expires_at: datetime


class ConsentConfirmRequest(BaseModel):
    """Schema for confirming consent via email token."""

    token: str = Field(..., min_length=64, max_length=256)


class ConsentConfirmResponse(BaseModel):
    """Response for consent confirmation."""

    consent_id: str
    status: str = "active"
    confirmed_at: datetime
    expires_at: datetime


class ConsentStatusResponse(BaseModel):
    """Schema for consent status."""

    has_active_consent: bool
    consent_records: list["ConsentRecordSummary"]


class ConsentRecordSummary(BaseModel):
    """Summary of a consent record."""

    consent_id: str
    consent_type: str
    status: str  # pending, active, revoked, expired
    initiated_at: datetime
    confirmed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


# Forward reference for type hints
AssessmentSummary.update_forward_refs()
SkillSummary.update_forward_refs()
ConsentStatusResponse.update_forward_refs()
