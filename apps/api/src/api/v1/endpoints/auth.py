"""Authentication endpoints: register, verify email, login.

Fix C-9 (2026-05-16 review):
1. `register()` referenced `request.<attr>` but `request` is the Starlette
   Request object — the Pydantic body is `request_data`. This 500'd on every
   call. Renamed accesses.
2. `login()` previously took `auth0_sub` as a request-body param, allowing
   anyone to impersonate any user. It now requires a valid JWT and derives
   the subject from the verified token.
3. Removed writes to non-existent model fields (`last_login_at`,
   `login_count`, `consent_confirmed_at`). Tracking those is now in
   `audit_log` (see `AuditService`).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.limiter import limiter
from src.core.security import verify_jwt
from src.models.models import ConsentRecord, User, UserRole
from src.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Inbound payload for `/auth/register`."""

    auth0_sub: str
    email: EmailStr
    display_name: str


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    needs_consent: bool


def _split_name(display_name: str) -> tuple[str, str]:
    """Best-effort split of a `display_name` into (first, last)."""
    parts = [p for p in display_name.strip().split() if p]
    if not parts:
        return ("", "")
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], " ".join(parts[1:]))


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def register(
    request_data: RegisterRequest,
    request: Request,  # noqa: ARG001  (kept for slowapi limiter)
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterResponse:
    """Create a new PADI.AI user linked to an Auth0 identity."""
    user_repo = UserRepository(db)

    existing = await user_repo.get_by_field("auth0_id", request_data.auth0_sub)
    if existing:
        return RegisterResponse(
            user_id=existing.id,
            email=existing.get_email() or "",
            needs_consent=not existing.is_active,
        )

    first_name, last_name = _split_name(request_data.display_name)
    new_user = User(
        auth0_id=request_data.auth0_sub,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.PARENT.value,
        is_active=True,
    )
    new_user.set_email(request_data.email)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RegisterResponse(
        user_id=new_user.id,
        email=new_user.get_email() or "",
        needs_consent=True,
    )


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],  # noqa: ARG001
) -> dict[str, str]:
    """Compatibility shim — Auth0 actually drives email verification."""
    if not token:
        raise HTTPException(status_code=400, detail="Missing verification token")
    return {"status": "email_verified", "next_step": "consent"}


@router.post("/login")
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_payload: Annotated[dict, Depends(verify_jwt)],
) -> dict[str, object]:
    """Confirm a logged-in Auth0 session against the local user record.

    The Auth0 `sub` is read from the verified JWT — never from the request
    body — to prevent impersonation.
    """
    auth0_sub = user_payload.get("sub")
    if not auth0_sub:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_field("auth0_id", auth0_sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check latest consent status using the column that actually exists
    # (`consented_at`, not `consent_confirmed_at`).
    consent_result = await db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user.id)
        .order_by(ConsentRecord.consented_at.desc().nullslast())
        .limit(1)
    )
    consent = consent_result.scalars().first()
    consent_completed = bool(consent and consent.consented_at)

    return {
        "user_id": user.id,
        "email": user.get_email() or "",
        "role": user.role,
        "consent_completed": consent_completed,
    }
