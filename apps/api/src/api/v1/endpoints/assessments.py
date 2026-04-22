"""
Assessment endpoints for diagnostic assessment flow.
"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import verify_jwt
from src.core.database import get_db
from src.services.audit_service import AuditService
from src.repositories.assessment_repository import (
    AssessmentRepository,
    AssessmentSessionRepository,
)
from src.repositories.student_repository import StudentRepository
from src.repositories.standard_repository import StandardRepository
from src.repositories.question_repository import QuestionRepository
from src.repositories.consent_repository import ConsentRepository
from src.services.assessment_service import (
    initialize_assessment_service,
    AssessmentService,
)
from src.schemas.assessment import (
    AssessmentStartRequest,
    AssessmentStartResponse,
    NextQuestionResponse,
    ResponseSubmission,
    ResponseSubmissionResponse,
    CompleteAssessmentResponse,
    AssessmentResultsResponse,
)
from src.core.limiter import limiter

router = APIRouter()
security = HTTPBearer()

logger = logging.getLogger(__name__)


def get_assessment_repository(
    db: Annotated[object, Depends(get_db)]
) -> AssessmentRepository:
    """Get assessment repository from database session."""
    return AssessmentRepository(db)


def get_session_repository(
    db: Annotated[object, Depends(get_db)]
) -> AssessmentSessionRepository:
    """Get session repository from database session."""
    return AssessmentSessionRepository(db)


def get_student_repository(
    db: Annotated[object, Depends(get_db)]
) -> StudentRepository:
    """Get student repository from database session."""
    return StudentRepository(db)


def get_standard_repository(
    db: Annotated[object, Depends(get_db)]
) -> StandardRepository:
    """Get standard repository from database session."""
    return StandardRepository(db)


def get_question_repository(
    db: Annotated[object, Depends(get_db)]
) -> QuestionRepository:
    """Get question repository from database session."""
    return QuestionRepository(db)


def get_consent_repository(
    db: Annotated[object, Depends(get_db)]
) -> ConsentRepository:
    """Get consent repository from database session."""
    return ConsentRepository(db)


def get_assessment_service(
    assessment_repository: AssessmentRepository = Depends(get_assessment_repository),
    session_repository: AssessmentSessionRepository = Depends(get_session_repository),
    student_repository: StudentRepository = Depends(get_student_repository),
    standard_repository: StandardRepository = Depends(get_standard_repository),
    question_repository: QuestionRepository = Depends(get_question_repository),
    consent_repository: ConsentRepository = Depends(get_consent_repository),
) -> AssessmentService:
    """Get initialized assessment service."""
    return initialize_assessment_service(
        assessment_repository=assessment_repository,
        session_repository=session_repository,
        student_repository=student_repository,
        standard_repository=standard_repository,
        question_repository=question_repository,
        consent_repository=consent_repository,
    )


@router.post(
    "/assessments",
    response_model=AssessmentStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start assessment",
    description="Start a new diagnostic assessment for a student.",
)
@limiter.limit("10/minute")
async def start_assessment(
    request_data: AssessmentStartRequest,
    request: Request,
    user_payload: dict = Depends(verify_jwt),
    service: AssessmentService = Depends(get_assessment_service),
    student_repository: StudentRepository = Depends(get_student_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Start assessment.

    - **student_id**: Student identifier
    - **assessment_type**: Assessment type (default: diagnostic)
    """
    # IDOR guard: verify the authenticated parent owns the requested student.
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    student = await student_repository.get_by_id(request_data.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.parent_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this student")

    try:
        result = await service.start_assessment(
            student_id=request_data.student_id,
            assessment_type=request_data.assessment_type,
        )
        # Audit: record assessment.started
        assessment_id = result.get("assessment_id") if isinstance(result, dict) else getattr(result, "assessment_id", None)
        await AuditService(db).record(
            user_id=user_id,
            action="assessment.started",
            resource_type="assessment",
            resource_id=str(assessment_id) if assessment_id else None,
            ip_address=ip,
            user_agent=ua,
        )
        await db.commit()
        return result
    except ValueError as e:
        error_detail = str(e)
        if "already has an active" in error_detail:
            raise HTTPException(status_code=400, detail=error_detail)
        elif "Active COPPA consent" in error_detail:
            raise HTTPException(status_code=403, detail=error_detail)
        raise HTTPException(status_code=400, detail=error_detail)


@router.get(
    "/assessments/{assessment_id}/next-question",
    response_model=NextQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get next question",
    description="Get the next question for an ongoing assessment.",
)
async def get_next_question(
    assessment_id: str,
    user_payload: dict = Depends(verify_jwt),
    service: AssessmentService = Depends(get_assessment_service),
    assessment_repository: AssessmentRepository = Depends(get_assessment_repository),
    student_repository: StudentRepository = Depends(get_student_repository),
):
    """
    Get next question.

    - **assessment_id**: Assessment identifier
    """
    # IDOR guard: verify the authenticated parent owns the assessment's student.
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    assessment = await assessment_repository.get_by_id(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    student = await student_repository.get_by_id(assessment.student_id)
    if student is None or student.parent_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this assessment")

    try:
        result = await service.get_next_question(
            assessment_id=assessment_id,
            student_id=assessment.student_id,
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting next question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/assessments/{assessment_id}/responses",
    response_model=ResponseSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit response",
    description="Submit a response to the current question.",
)
async def submit_response(
    assessment_id: str,
    request_data: ResponseSubmission,
    user_payload: dict = Depends(verify_jwt),
    service: AssessmentService = Depends(get_assessment_service),
):
    """
    Submit response.

    - **assessment_id**: Assessment identifier
    - **question_id**: Question identifier
    - **selected_answer**: Selected option (A-D) or numeric answer
    - **time_spent_ms**: Time spent on question in milliseconds
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")

    try:
        result = await service.submit_response(
            assessment_id=assessment_id,
            student_id=user_id,
            question_id=request_data.question_id,
            selected_answer=request_data.selected_answer,
            time_spent_ms=request_data.time_spent_ms,
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/assessments/{assessment_id}/complete",
    response_model=CompleteAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete assessment",
    description="Complete an ongoing assessment.",
)
async def complete_assessment(
    assessment_id: str,
    request: Request,
    user_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
    service: AssessmentService = Depends(get_assessment_service),
):
    """
    Complete assessment.

    - **assessment_id**: Assessment identifier
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    try:
        result = await service.complete_assessment(
            assessment_id=assessment_id,
            db_session=db,
        )
        # Audit: record assessment.completed
        await AuditService(db).record(
            user_id=user_id,
            action="assessment.completed",
            resource_type="assessment",
            resource_id=assessment_id,
            ip_address=ip,
            user_agent=ua,
        )
        await db.commit()
        return result
    except HTTPException:
        raise
    except ValueError as e:
        if "Minimum 35 questions" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing assessment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/assessments/{assessment_id}/results",
    response_model=AssessmentResultsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get results",
    description="Get assessment results after completion.",
)
async def get_results(
    assessment_id: str,
    user_payload: dict = Depends(verify_jwt),
    service: AssessmentService = Depends(get_assessment_service),
    assessment_repository: AssessmentRepository = Depends(get_assessment_repository),
    student_repository: StudentRepository = Depends(get_student_repository),
):
    """
    Get assessment results.

    - **assessment_id**: Assessment identifier
    """
    # IDOR guard: verify the authenticated parent owns the assessment's student.
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    assessment = await assessment_repository.get_by_id(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    student = await student_repository.get_by_id(assessment.student_id)
    if student is None or student.parent_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this assessment")

    try:
        result = await service.get_results(
            assessment_id=assessment_id,
            student_id=assessment.student_id,
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
