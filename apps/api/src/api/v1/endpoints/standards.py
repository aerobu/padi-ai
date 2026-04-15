"""
Standards endpoints for Oregon math standards.
"""

import logging
import re
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import verify_jwt
from src.repositories.standard_repository import StandardRepository
from src.schemas.standard import (
    StandardQueryParams,
    StandardListItem,
    StandardListResponse,
    StandardDetailResponse,
)

router = APIRouter()
security = HTTPBearer()

logger = logging.getLogger(__name__)


def extract_cluster_from_code(standard_code: str) -> str:
    """
    Extract cluster identifier from standard code.

    Standard code format: "4.NBT.A.1" -> cluster = "A"
    Example: 4.NBT.A.1 -> "4.NBT.A"
    """
    parts = standard_code.split('.')
    if len(parts) >= 3:
        # Return grade.domain.cluster (e.g., "4.NBT.A")
        return '.'.join(parts[:3])
    return standard_code


def calculate_difficulty(standard_code: str) -> float:
    """
    Calculate estimated difficulty based on standard code complexity.

    Higher grade levels and more specific standards get higher difficulty.
    Returns difficulty on scale 1.0-5.0.
    """
    parts = standard_code.split('.')
    if not parts:
        return 3.0

    try:
        grade = int(parts[0])
    except (ValueError, IndexError):
        return 3.0

    # Base difficulty on grade level (1-5)
    # Grade 1 = 1.5, Grade 5 = 4.0
    base_difficulty = 1.5 + (grade - 1) * 0.625

    # Adjust based on specificity of cluster
    if len(parts) >= 4:
        # More specific standards are slightly harder
        base_difficulty += 0.5

    return min(5.0, round(base_difficulty, 1))


def get_standard_repository(
    db: Annotated[object, Depends(get_db)]
) -> StandardRepository:
    """Get standard repository from database session."""
    return StandardRepository(db)


@router.get(
    "/standards",
    response_model=StandardListResponse,
    status_code=status.HTTP_200_OK,
    summary="List standards",
    description="Get Oregon math standards by grade and domain.",
)
async def list_standards(
    params: StandardQueryParams = Depends(),
    standard_repository: StandardRepository = Depends(get_standard_repository),
):
    """
    List standards.

    - **grade**: Grade level (1-5), default 4
    - **domain**: Optional domain filter
    - **include_prerequisites**: Include prerequisite relationships
    """
    # Get standards
    standards = await standard_repository.get_by_grade(params.grade)

    if params.domain:
        standards = [s for s in standards if s.domain == params.domain]

    return StandardListResponse(
        standards=[
            StandardListItem(
                code=s.standard_code,
                domain=s.domain,
                cluster=extract_cluster_from_code(s.standard_code),
                title=s.title,
                description=s.description,
                cognitive_level="analyze",  # Default cognitive level for standards
                estimated_difficulty=calculate_difficulty(s.standard_code),  # Based on standard code complexity
            )
            for s in standards
        ],
        total=len(standards),
    )


@router.get(
    "/standards/{standard_code}",
    response_model=StandardDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get standard",
    description="Get standard details by code.",
)
async def get_standard(
    standard_code: str,
    standard_repository: StandardRepository = Depends(get_standard_repository),
):
    """
    Get standard details.

    - **standard_code**: Standard code (e.g., "4.NBT.A.1")
    """
    # Get standard
    standard = await standard_repository.get_by_code(standard_code)
    if not standard:
        raise HTTPException(
            status_code=404,
            detail=f"Standard '{standard_code}' not found",
        )

    # Get prerequisites
    prerequisites = await standard_repository.get_prerequisites(standard.id)

    # Get dependents
    dependents = await standard_repository.get_dependents(standard.id)

    # Get question count
    question_count = await standard_repository.get_question_count(standard.id)

    return StandardDetailResponse(
        code=standard.standard_code,
        domain=standard.domain,
        cluster=extract_cluster_from_code(standard.standard_code),
        title=standard.title,
        description=standard.description,
        cognitive_level="analyze",  # Default cognitive level for standards
        estimated_difficulty=calculate_difficulty(standard.standard_code),  # Based on standard code complexity
        bkt={
            "p_l0": 0.0,
            "p_trans": 0.5,
            "p_slip": 0.2,
            "p_guess": 0.25,
        },
        prerequisites=[{"prerequisite_code": p} for p in prerequisites],
        dependent_standards=dependents,
        question_count=question_count,
    )
