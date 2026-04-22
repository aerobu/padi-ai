"""
Consent endpoints for COPPA compliance.
"""

import logging
from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_jwt
from src.core.database import get_db
from src.repositories.consent_repository import ConsentRepository
from src.services.consent_service import initialize_consent_service, ConsentService
from src.services.audit_service import AuditService
from src.clients.ses_client import SESClient, get_ses_client
from src.schemas.user import (
    ConsentInitiateRequest,
    ConsentInitiateResponse,
    ConsentConfirmRequest,
    ConsentConfirmResponse,
    ConsentStatusResponse,
)
from src.core.limiter import limiter

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_consent_repository(
    db: Annotated[object, Depends(get_db)]
) -> ConsentRepository:
    """Get consent repository from database session."""
    return ConsentRepository(db)


def get_consent_service(
    consent_repository: ConsentRepository = Depends(get_consent_repository),
    ses_client: SESClient = Depends(get_ses_client),
) -> ConsentService:
    """Get initialized consent service."""
    return initialize_consent_service(consent_repository, ses_client)


@router.post(
    "/consent/initiate",
    response_model=ConsentInitiateResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate COPPA consent",
    description="Start the COPPA consent process for a parent.",
)
@limiter.limit("5/minute")
async def initiate_consent(
    request_data: ConsentInitiateRequest,
    request: Request,
    user_payload: dict = Depends(verify_jwt),
    consent_service: ConsentService = Depends(get_consent_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate COPPA consent.

    - **student_display_name**: Name of the student
    - **acknowledgements**: List of acknowledged consent clauses
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    email = user_payload.get("email", "parent@example.com")

    # Get IP address and user-agent for audit trail
    ip_address = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("user-agent")

    try:
        result = await consent_service.initiate_consent(
            user_id=user_id,
            student_display_name=request_data.student_display_name,
            acknowledgements=request_data.acknowledgements,
            ip_address=ip_address,
            email=email,
        )
        # Audit: record consent.initiated after successful action
        consent_id = result.get("consent_id") if isinstance(result, dict) else getattr(result, "consent_id", None)
        await AuditService(db).record(
            user_id=user_id,
            action="consent.initiated",
            resource_type="consent",
            resource_id=str(consent_id) if consent_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/consent/confirm",
    response_model=ConsentConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm COPPA consent",
    description="Confirm consent via email verification token.",
)
async def confirm_consent(
    request: ConsentConfirmRequest,
    http_request: Request,
    consent_service: ConsentService = Depends(get_consent_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm consent using email token.

    This endpoint is called from an email link.
    """
    ip = http_request.client.host if http_request.client else None
    ua = http_request.headers.get("user-agent")

    try:
        result = await consent_service.confirm_consent(request.token)
        # Audit: record consent.granted — this is the actual grant moment
        consent_id = result.get("consent_id") if isinstance(result, dict) else getattr(result, "consent_id", None)
        # Look up user_id from the confirmed consent record
        consent_record = await consent_service.consent_repository.get_by_id(str(consent_id)) if consent_id else None
        user_id = consent_record.user_id if consent_record else None
        await AuditService(db).record(
            user_id=user_id,
            action="consent.granted",
            resource_type="consent",
            resource_id=str(consent_id) if consent_id else None,
            ip_address=ip,
            user_agent=ua,
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/consent/status",
    response_model=ConsentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get consent status",
    description="Check consent status for the authenticated user.",
)
async def get_consent_status(
    user_payload: dict = Depends(verify_jwt),
    consent_repository: ConsentRepository = Depends(get_consent_repository),
):
    """
    Get consent status.
    """
    user_id = user_payload.get("sub") or user_payload.get("auth0_id")
    service = initialize_consent_service(consent_repository)

    try:
        result = await service.get_consent_status(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting consent status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
