"""
Assessment endpoints for diagnostic assessment flow.
"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import verify_jwt
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
async def start_assessment(
    request: AssessmentStartRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AssessmentService = Depends(get_assessment_service),
):
    """
    Start assessment.

    - **student_id**: Student identifier
    - **assessment_type**: Assessment type (default: diagnostic)
    """
    # Verify JWT
    user_payload = verify_jwt(credentials)

    try:
        result = await service.start_assessment(
            student_id=request.student_id,
            assessment_type=request.assessment_type,
        )
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AssessmentService = Depends(get_assessment_service),
):
    """
    Get next question.

    - **assessment_id**: Assessment identifier
    """
    # Verify JWT
    user_payload = verify_jwt(credentials)

    try:
        result = await service.get_next_question(
            assessment_id=assessment_id,
            student_id=user_payload["sub"],
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting next question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/assessments/{assessment_id}/responses",
    response_model=ResponseSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit response",
    description="Submit a response to the current question.",
)
async def submit_response(
    assessment_id: str,
    request: ResponseSubmission,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AssessmentService = Depends(get_assessment_service),
):
    """
    Submit response.

    - **assessment_id**: Assessment identifier
    - **question_id**: Question identifier
    - **selected_answer**: Selected option (A-D) or numeric answer
    - **time_spent_ms**: Time spent on question in milliseconds
    """
    # Verify JWT
    user_payload = verify_jwt(credentials)

    try:
        result = await service.submit_response(
            assessment_id=assessment_id,
            student_id=user_payload["sub"],
            question_id=request.question_id,
            selected_answer=request.selected_answer,
            time_spent_ms=request.time_spent_ms,
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/assessments/{assessment_id}/complete",
    response_model=CompleteAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete assessment",
    description="Complete an ongoing assessment.",
)
async def complete_assessment(
    assessment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AssessmentService = Depends(get_assessment_service),
):
    """
    Complete assessment.

    - **assessment_id**: Assessment identifier
    """
    # Verify JWT
    user_payload = verify_jwt(credentials)

    try:
        result = await service.complete_assessment(assessment_id=assessment_id)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        if "Minimum 35 questions" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assessments/{assessment_id}/results",
    response_model=AssessmentResultsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get results",
    description="Get assessment results after completion.",
)
async def get_results(
    assessment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AssessmentService = Depends(get_assessment_service),
):
    """
    Get assessment results.

    - **assessment_id**: Assessment identifier
    """
    # Verify JWT
    user_payload = verify_jwt(credentials)

    try:
        result = await service.get_results(
            assessment_id=assessment_id,
            student_id=user_payload["sub"],
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))
