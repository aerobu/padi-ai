"""
Student endpoints for parent-managed student profiles.
"""

import logging
from typing import Annotated
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_jwt
from src.core.database import get_db
from src.repositories.student_repository import StudentRepository
from src.repositories.consent_repository import ConsentRepository
from src.services.audit_service import AuditService
from src.schemas.user import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDetailResponse,
)

router = APIRouter()

logger = logging.getLogger(__name__)


def get_student_repository(
    db: Annotated[object, Depends(get_db)]
) -> StudentRepository:
    """Get student repository from database session."""
    return StudentRepository(db)


def get_consent_repository(
    db: Annotated[object, Depends(get_db)]
) -> ConsentRepository:
    """Get consent repository from database session."""
    return ConsentRepository(db)


@router.post(
    "/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student",
    description="Create a new student profile for the authenticated parent.",
)
async def create_student(
    student_data: StudentCreate,
    http_request: Request,
    user_payload: dict = Depends(verify_jwt),
    student_repository: StudentRepository = Depends(get_student_repository),
    consent_repository: ConsentRepository = Depends(get_consent_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a student.

    **Requires**: Active COPPA consent from parent.
    - **display_name**: Student's display name (1-50 chars)
    - **grade_level**: Grade level (1-5)
    - **avatar_id**: Avatar identifier
    - **birth_year**: Optional birth year (2012-2024)
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    ip = http_request.client.host if http_request.client else None
    ua = http_request.headers.get("user-agent")

    # Check active consent
    has_consent = await consent_repository.has_active_consent(user_id)
    if not has_consent:
        raise HTTPException(
            status_code=403,
            detail="Active COPPA consent required to create student",
        )

    # Create student
    try:
        student = await student_repository.create({
            "id": str(uuid4()),
            "parent_id": user_id,
            "display_name": student_data.display_name,
            "grade_level": student_data.grade_level,
            "avatar_id": student_data.avatar_id,
            "birth_year": student_data.birth_year,
        })
        # Audit: record student.created
        await AuditService(db).record(
            user_id=user_id,
            action="student.created",
            resource_type="student",
            resource_id=student.id,
            ip_address=ip,
            user_agent=ua,
        )
        await db.commit()
        return StudentResponse(
            student_id=student.id,
            display_name=student.display_name,
            grade_level=student.grade_level,
            avatar_id=student.avatar_id,
            birth_year=student.birth_year,
            is_active=True,
            created_at=student.created_at,
        )
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/students/{student_id}",
    response_model=StudentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student",
    description="Get student details by ID.",
)
async def get_student(
    student_id: str,
    user_payload: dict = Depends(verify_jwt),
    student_repository: StudentRepository = Depends(get_student_repository),
):
    """
    Get student details.

    - **student_id**: Student identifier
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")

    # Get student with latest assessment
    student = await student_repository.get_with_latest_assessment(student_id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    # Verify ownership
    if student.parent_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    # Get skill summary
    skill_summary = await student_repository.update_skill_summary(student_id)

    return StudentDetailResponse(
        student_id=student.id,
        display_name=student.display_name,
        grade_level=student.grade_level,
        avatar_id=student.avatar_id,
        birth_year=student.birth_year,
        is_active=student.is_active,
        created_at=student.created_at,
        latest_assessment=student.latest_assessment,
        skill_summary=skill_summary,
    )


@router.put(
    "/students/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update student",
    description="Update student profile.",
)
async def update_student(
    student_id: str,
    update_data: StudentUpdate,
    http_request: Request,
    user_payload: dict = Depends(verify_jwt),
    student_repository: StudentRepository = Depends(get_student_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update student.

    - **student_id**: Student identifier
    - **display_name**: New display name (optional)
    - **avatar_id**: New avatar (optional)
    - **grade_level**: New grade level (optional, 1-5)
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    ip = http_request.client.host if http_request.client else None
    ua = http_request.headers.get("user-agent")

    # Get existing student
    student = await student_repository.get_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    # Verify ownership
    if student.parent_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    # Build update dict
    updates = {}
    if update_data.display_name is not None:
        updates["display_name"] = update_data.display_name
    if update_data.avatar_id is not None:
        updates["avatar_id"] = update_data.avatar_id
    if update_data.grade_level is not None:
        updates["grade_level"] = update_data.grade_level

    # Update student
    updated_student = await student_repository.update(student_id, updates)

    # Audit: record student.updated
    await AuditService(db).record(
        user_id=user_id,
        action="student.updated",
        resource_type="student",
        resource_id=student_id,
        ip_address=ip,
        user_agent=ua,
    )
    await db.commit()

    return StudentResponse(
        student_id=updated_student.id,
        display_name=updated_student.display_name,
        grade_level=updated_student.grade_level,
        avatar_id=updated_student.avatar_id,
        birth_year=updated_student.birth_year,
        is_active=updated_student.is_active,
        created_at=updated_student.created_at,
    )


@router.get(
    "/students",
    response_model=list[StudentResponse],
    status_code=status.HTTP_200_OK,
    summary="List students",
    description="Get all students for the authenticated parent.",
)
async def list_students(
    user_payload: dict = Depends(verify_jwt),
    student_repository: StudentRepository = Depends(get_student_repository),
):
    """
    List all students for the authenticated parent.
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")

    # Get all students
    students = await student_repository.get_by_parent_id(user_id)

    return [
        StudentResponse(
            student_id=s.id,
            display_name=s.display_name,
            grade_level=s.grade_level,
            avatar_id=s.avatar_id,
            birth_year=s.birth_year,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in students
    ]
