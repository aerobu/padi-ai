"""
Consent endpoints for COPPA compliance.
"""

import logging
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.security import verify_jwt
from src.repositories.consent_repository import ConsentRepository
from src.services.consent_service import initialize_consent_service
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
    consent_repository: ConsentRepository = Depends(get_consent_repository),
):
    """
    Initiate COPPA consent.

    - **student_display_name**: Name of the student
    - **acknowledgements**: List of acknowledged consent clauses
    """
    # Verify JWT
    user_payload = verify_jwt(credentials)

    # TODO: Get email from JWT or user table
    email = user_payload.get("email", "parent@example.com")

    # Get IP address
    ip_address = (
        req.client.host if req.client else "0.0.0.0"
    )

    # Initialize service
    service = initialize_consent_service(consent_repository)

    try:
        result = await service.initiate_consent(
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
    consent_repository: ConsentRepository = Depends(get_consent_repository),
):
    """
    Confirm consent using email token.

    This endpoint is called from an email link.
    """
    service = initialize_consent_service(consent_repository)

    try:
        result = await service.confirm_consent(request.token)
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
