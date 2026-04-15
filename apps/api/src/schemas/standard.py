"""
Pydantic schemas for Standard model.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class StandardQueryParams(BaseModel):
    """Query parameters for listing standards."""

    grade: int = Field(default=4, ge=1, le=5)
    domain: Optional[str] = Field(default=None)
    include_prerequisites: bool = False


class StandardListItem(BaseModel):
    """List item representation of a standard."""

    code: str
    domain: str
    cluster: str
    title: str
    description: str
    cognitive_level: str
    estimated_difficulty: float


class StandardListResponse(BaseModel):
    """Response for listing standards."""

    standards: List[StandardListItem]
    total: int


class StandardDetailResponse(BaseModel):
    """Detailed standard information."""

    code: str
    domain: str
    cluster: str
    title: str
    description: str
    cognitive_level: str
    estimated_difficulty: float
    bkt_defaults: "BKTDefaults"
    prerequisites: List["PrerequisiteRelation"]
    dependent_standards: List[str]
    question_count: int


class BKTDefaults(BaseModel):
    """BKT initialization defaults for a standard."""

    p_l0: float  # Initial mastery probability
    p_transit: float  # Transition probability
    p_slip: float  # Slip probability
    p_guess: float  # Guess probability


class PrerequisiteRelation(BaseModel):
    """Prerequisite relationship."""

    prerequisite_code: str
    relationship_type: str
    strength: float
