"""
Authentication endpoints: register, verify email, login.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from src.core.database import get_db
from src.core.security import verify_jwt
from src.core.encryption import EncryptionService
from src.models.models import User, UserRole, ConsentRecord, ConsentStatus
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    auth0_sub: str
    email: EmailStr
    display_name: str


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    needs_consent: bool


from src.core.limiter import limiter
from fastapi import Request

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new PADI.AI user linked to Auth0.
    Called after Auth0 signup (post-Auth0 redirect).

    Returns: user_id and flag indicating consent is required.
    """
    user_repo = UserRepository(db)

    # Check if user already exists
    existing = await user_repo.get_by_field("auth0_id", request.auth0_sub)
    if existing:
        return RegisterResponse(
            user_id=existing.id,
            email=existing.get_email() or "",
            needs_consent=not existing.is_active,
        )

    # Create new user
    new_user = User(
        auth0_id=request.auth0_sub,
        display_name=request.display_name,
        first_name=request.display_name.split()[0] if " " in request.display_name else request.display_name,
        last_name=request.display_name.split()[-1] if " " in request.display_name else "",
        role=UserRole.PARENT.value,
        is_active=True,
    )

    # Encrypt email
    new_user.set_email(request.email)

    # Save to database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RegisterResponse(
        user_id=new_user.id,
        email=new_user.get_email() or "",
        needs_consent=True,  # Always require consent for new users
    )


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email after Auth0 sends verification email.
    Token is provided by Auth0.

    In practice, Auth0 handles email verification.
    This endpoint is for compatibility with flow spec.
    """
    # For now, validate that token is present (Auth0 provides this)
    # In a real implementation, validate token expiry and format
    if not token:
        raise HTTPException(status_code=400, detail="Missing verification token")

    # For compatibility with Auth0 flow, just confirm
    return {"status": "email_verified", "next_step": "consent"}


@router.post("/login")
async def login(
    auth0_sub: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Login endpoint (stub - Auth0 handles real login).
    Called after Auth0 provides tokens.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_field("auth0_id", auth0_sub)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update last login
    user.last_login_at = datetime.utcnow()
    user.login_count = getattr(user, "login_count", 0) + 1
    db.add(user)
    await db.commit()

    # Check actual consent status
    consent_result = await db.execute(
        select(ConsentRecord)
        .filter(ConsentRecord.user_id == user.id)
        .order_by(ConsentRecord.created_at.desc())
        .limit(1)
    )
    consent = consent_result.scalars().first()
    consent_completed = consent.consent_confirmed_at is not None if consent else False

    return {
        "user_id": user.id,
        "email": user.get_email() or "",
        "role": user.role,
        "consent_completed": consent_completed,
    }
