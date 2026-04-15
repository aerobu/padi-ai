"""
Standards endpoints for Oregon math standards.
"""

import logging
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
                cluster="",  # TODO: Extract from code
                title=s.title,
                description=s.description,
                cognitive_level="basic",  # TODO: Implement
                estimated_difficulty=3.0,  # TODO: Implement
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
        cluster="",  # TODO: Extract from code
        title=standard.title,
        description=standard.description,
        cognitive_level="basic",  # TODO: Implement
        estimated_difficulty=3.0,  # TODO: Implement
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
