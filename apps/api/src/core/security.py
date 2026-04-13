"""
Security utilities for PADI.AI API.
Auth0 JWT validation and user authentication.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_settings

security = HTTPBearer(auto_error=False)
settings = get_settings()


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials,
) -> dict:
    """
    Verify Auth0 JWT token and return user payload.

    Args:
        credentials: HTTP Authorization credentials containing Bearer token

    Returns:
        dict: Decoded JWT payload with user info

    Raises:
        HTTPException: If token is invalid or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided",
        )

    token = credentials.credentials

    try:
        # Decode and verify JWT
        # Note: In production, use PyJWKClient for key rotation support
        payload = jwt.decode(
            token,
            settings.AUTH0_SECRET,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE or settings.AUTH0_CLIENT_ID,
            issuer=settings.AUTH0_ISSUER_BASE_URL,
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid issuer",
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid audience",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


def create_jwt_response(token: str, expires_in: int = 3600) -> dict:
    """
    Create a standardized JWT response.

    Args:
        token: JWT token string
        expires_in: Token expiration time in seconds

    Returns:
        dict: Standardized JWT response
    """
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "expires_at": datetime.utcnow() + timedelta(seconds=expires_in),
    }


def generate_nonce() -> str:
    """
    Generate a random nonce for OpenID Connect.
    Used to prevent replay attacks during authentication.

    Returns:
        str: Random nonce string
    """
    import secrets

    return secrets.token_urlsafe(32)


def validate_email(email: str) -> bool:
    """
    Basic email validation.

    Args:
        email: Email address to validate

    Returns:
        bool: True if email format is valid
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None
