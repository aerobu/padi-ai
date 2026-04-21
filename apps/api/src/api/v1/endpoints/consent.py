"""
Consent endpoints for COPPA compliance.
"""

import logging
from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import verify_jwt
from src.core.database import get_db
from src.repositories.consent_repository import ConsentRepository
from src.services.consent_service import initialize_consent_service, ConsentService
from src.clients.ses_client import SESClient, get_ses_client
from src.schemas.user import (
    ConsentInitiateRequest,
    ConsentInitiateResponse,
    ConsentConfirmRequest,
    ConsentConfirmResponse,
    ConsentStatusResponse,
)

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
async def initiate_consent(
    request_data: ConsentInitiateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    req: Request = Depends(),
    consent_service: ConsentService = Depends(get_consent_service),
):
    """
    Initiate COPPA consent.

    - **student_display_name**: Name of the student
    - **acknowledgements**: List of acknowledged consent clauses
    """
    # Verify JWT
    user_payload = verify_jwt(credentials)

    # Get email from JWT payload
    email = user_payload.get("email", "parent@example.com")

    # Get IP address
    ip_address = (
        req.client.host if req.client else "0.0.0.0"
    )

    try:
        result = await consent_service.initiate_consent(
            user_id=user_payload["sub"],
            student_display_name=request_data.student_display_name,
            acknowledgements=request_data.acknowledgements,
            ip_address=ip_address,
            email=email,
        )
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
    consent_service: ConsentService = Depends(get_consent_service),
):
    """
    Confirm consent using email token.

    This endpoint is called from an email link.
    """
    try:
        result = await consent_service.confirm_consent(request.token)
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    consent_repository: ConsentRepository = Depends(get_consent_repository),
):
    """
    Get consent status.
    """
    user_payload = verify_jwt(credentials)

    service = initialize_consent_service(consent_repository)

    try:
        result = await service.get_consent_status(user_payload["sub"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
