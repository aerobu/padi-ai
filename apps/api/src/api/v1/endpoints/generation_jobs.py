"""
Generation Jobs endpoints for AI question generation.
"""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from src.core.database import get_db
from src.core.security import verify_jwt
from src.repositories.generation_job_repository import GenerationJobRepository
from src.services.llm_question_generator import LLMQuestionGenerator
from src.schemas.generation_job import (
    GenerationJobCreateRequest,
    GenerationJobListResponse,
    GenerationJobDetailResponse,
    ExecuteJobResponse,
    ReviewQueueResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_generation_job_repository(
    db: Annotated[object, Depends(get_db)]
) -> GenerationJobRepository:
    """Get generation job repository from database session."""
    return GenerationJobRepository(db)


async def get_llm_generator(
    db: Annotated[object, Depends(get_db)]
) -> LLMQuestionGenerator:
    """Get LLM question generator from database session."""
    return LLMQuestionGenerator(db)


def get_user_from_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
) -> dict:
    """Get current authenticated user from JWT credentials.

    The verify_jwt dependency already decodes the JWT and returns the payload,
    so this function simply returns the already-decoded payload.
    """
    # credentials is already the decoded payload from verify_jwt dependency
    return credentials


@router.post(
    "/admin/generation-jobs",
    status_code=status.HTTP_201_CREATED,
    summary="Create generation job",
    description="Create a new AI question generation job.",
)
async def create_generation_job(
    request: GenerationJobCreateRequest,
    db: Annotated[object, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
    job_repo: Annotated[GenerationJobRepository, Depends(get_generation_job_repository)],
) -> dict:
    """
    Create a new generation job.

    The job will be queued for processing by the LLM question generator.
    """
    try:
        user_id = user_payload.get("sub") or user_payload.get("auth0_id")

        job = await job_repo.create({
            "id": str(__import__("uuid").uuid4()),
            "standard_code": request.standard_code,
            "requested_count": request.requested_count,
            "difficulty_levels": request.difficulty_levels or [1, 2, 3, 4, 5],
            "context_themes": request.context_themes,
            "model": "o3-mini",
            "created_by": user_id,
            "created_at": __import__("datetime").datetime.utcnow(),
            "updated_at": __import__("datetime").datetime.utcnow(),
        })

        return {
            "job_id": job.id,
            "standard_code": job.standard_code,
            "requested_count": job.requested_count,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }

    except Exception as e:
        logger.error(f"Error creating generation job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating generation job: {str(e)}",
        )


@router.get(
    "/admin/generation-jobs",
    summary="List generation jobs",
    description="List all generation jobs with optional filters.",
)
async def list_generation_jobs(
    db: Annotated[object, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
    job_repo: Annotated[GenerationJobRepository, Depends(get_generation_job_repository)],
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    List generation jobs.

    Returns paginated list of jobs with optional status filter.
    """
    try:
        # Verify admin access
        if user_payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        jobs = await job_repo.get_all(
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        return {
            "jobs": [
                {
                    "id": job.id,
                    "standard_code": job.standard_code,
                    "requested_count": job.requested_count,
                    "difficulty_levels": job.difficulty_levels,
                    "status": job.status,
                    "total_generated": job.total_generated,
                    "auto_approved": job.auto_approved,
                    "needs_review": job.needs_review,
                    "failed_validation": job.failed_validation,
                    "estimated_cost_usd": job.estimated_cost_usd,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                }
                for job in jobs
            ],
            "total": len(jobs),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing generation jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing generation jobs: {str(e)}",
        )


@router.get(
    "/admin/generation-jobs/{job_id}",
    summary="Get generation job",
    description="Get details of a specific generation job.",
)
async def get_generation_job(
    job_id: str,
    db: Annotated[object, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
    job_repo: Annotated[GenerationJobRepository, Depends(get_generation_job_repository)],
    limit: int = 50,
) -> dict:
    """
    Get details of a generation job including generated questions.
    """
    try:
        # Verify admin access
        if user_payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        from src.models.models import GeneratedQuestion

        job = await job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Get generated questions for this job
        result = await db.execute(
            select(GeneratedQuestion)
            .where(GeneratedQuestion.job_id == job_id)
            .limit(50)
        )
        questions = result.scalars().all()

        return {
            "job": {
                "id": job.id,
                "standard_code": job.standard_code,
                "requested_count": job.requested_count,
                "difficulty_levels": job.difficulty_levels,
                "context_themes": job.context_themes,
                "model": job.model,
                "status": job.status,
                "total_generated": job.total_generated,
                "auto_approved": job.auto_approved,
                "needs_review": job.needs_review,
                "failed_validation": job.failed_validation,
                "error_message": job.error_message,
                "estimated_cost_usd": job.estimated_cost_usd,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "created_at": job.created_at.isoformat() if job.created_at else None,
            },
            "questions": [
                {
                    "id": q.id,
                    "stem": q.stem,
                    "difficulty": q.difficulty,
                    "validation_status": q.validation_status,
                    "confidence_score": q.confidence_score,
                    "promoted": q.promoted_to_question_id is not None,
                }
                for q in questions
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting generation job: {str(e)}",
        )


@router.post(
    "/admin/generation-jobs/{job_id}/execute",
    summary="Execute generation job",
    description="Execute a queued generation job.",
)
async def execute_generation_job(
    job_id: str,
    db: Annotated[object, Depends(get_db)],
    llm_generator: Annotated[LLMQuestionGenerator, Depends(get_llm_generator)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
) -> dict:
    """
    Execute a queued generation job.

    This triggers the LLM to generate questions for the job.
    """
    try:
        # Verify admin access
        if user_payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        job = await llm_generator.job_repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        if job.status != "queued":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job must be in 'queued' status, current status: {job.status}",
            )

        # Execute job
        updated_job = await llm_generator.execute_generation_job(job_id)

        return {
            "job_id": updated_job.id,
            "status": updated_job.status,
            "total_generated": updated_job.total_generated,
            "auto_approved": updated_job.auto_approved,
            "needs_review": updated_job.needs_review,
            "completed_at": updated_job.completed_at.isoformat()
            if updated_job.completed_at
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing generation job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing generation job: {str(e)}",
        )


@router.get(
    "/admin/review-queue",
    summary="Get review queue",
    description="Get questions pending human review.",
)
async def get_review_queue(
    db: Annotated[object, Depends(get_db)],
    user_payload: Annotated[dict, Depends(get_user_from_credentials)],
    limit: int = 50,
) -> dict:
    """
    Get questions pending human review.
    """
    try:
        # Verify admin access
        if user_payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        from src.models.models import ContentReviewQueue

        result = await db.execute(
            select(ContentReviewQueue)
            .where(ContentReviewQueue.status == "pending")
            .order_by(ContentReviewQueue.priority.desc())
            .limit(limit)
        )
        review_items = result.scalars().all()

        return {
            "review_queue": [
                {
                    "id": item.id,
                    "generated_question_id": item.generated_question_id,
                    "priority": item.priority,
                    "confidence_score": item.confidence_score,
                    "flags": item.flags,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in review_items
            ],
            "total": len(review_items),
        }

    except Exception as e:
        logger.error(f"Error getting review queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting review queue: {str(e)}",
        )
