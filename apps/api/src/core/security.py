"""
Security utilities for PADI.AI API.
Auth0 JWT validation and user authentication.
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_settings

security = HTTPBearer(auto_error=False)
settings = get_settings()

# Initialize JWKS client (cached globally)
_jwks_client = None


def get_jwks_client():
    """Get or create the JWKS client for Auth0."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.AUTH0_ISSUER_BASE_URL}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


async def verify_jwt(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> dict:
    """
    Verify Auth0 JWT token using RS256 with JWKS public key.

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
        # Get the public key from Auth0 JWKS endpoint
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)

        # Decode the token using the public key
        payload = jwt.decode(
            token,
            signing_key.key,
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
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
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
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
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
