"""
COPPA consent service for managing parental consent workflows.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from pydantic import EmailStr

from src.repositories.consent_repository import ConsentRepository
from src.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class ConsentService:
    """Service for COPPA consent management."""

    # Consent token expiration (48 hours)
    TOKEN_EXPIRY_HOURS = 48

    def __init__(self, consent_repository: ConsentRepository):
        """
        Initialize consent service.

        Args:
            consent_repository: Repository for consent records
        """
        self.consent_repository = consent_repository
        self.redis_client = get_redis_client()

    async def initiate_consent(
        self,
        user_id: str,
        student_display_name: str,
        acknowledgements: list[str],
        ip_address: str,
        email: str,
    ) -> Dict[str, Any]:
        """
        Initiate COPPA consent process.

        Args:
            user_id: Parent/user ID
            student_display_name: Name of student
            acknowledgements: List of acknowledged consent clauses
            ip_address: User's IP for audit trail
            email: Parent's email (for sending verification)

        Returns:
            Consent initiation response
        """
        # Check for existing active consent
        existing = await self.consent_repository.get_active_consent_for_user(user_id)
        if existing:
            raise ValueError("Active consent already exists for this parent")

        # Verify all acknowledgements are provided
        required_clauses = [
            "data_collection",
            "data_use",
            "third_party_disclosure",
            "parental_rights",
        ]
        if not all(clause in acknowledgements for clause in required_clauses):
            raise ValueError("All required consent clauses must be acknowledged")

        # Generate verification token
        token = secrets.token_hex(32)

        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(hours=self.TOKEN_EXPIRY_HOURS)

        # Store token in Redis (for email link verification)
        await self.redis_client.set(
            f"consent:token:{token}",
            {
                "user_id": user_id,
                "student_name": student_display_name,
                "expires_at": expires_at.isoformat(),
            },
            ex=self.TOKEN_EXPIRY_HOURS * 3600,
        )

        # Mask email for response
        masked_email = self._mask_email(email)

        # Create pending consent record
        record = await self.consent_repository.create_pending_consent(
            user_id=user_id,
            student_id=None,  # To be set after student creation
            consent_type="coppa_verifiable",
            token=token,
            expires_at=expires_at,
        )

        logger.info(
            f"Consent initiated for user {user_id}, "
            f"token: {token[:8]}..., expires: {expires_at}"
        )

        return {
            "consent_id": record.id,
            "status": "pending",
            "verification_method": "email_plus",
            "email_sent_to": masked_email,
            "expires_at": expires_at,
            "verification_token": token,  # In production, send via email only
        }

    async def confirm_consent(
        self, token: str
    ) -> Dict[str, Any]:
        """
        Confirm consent via email verification token.

        Args:
            token: Verification token from email link

        Returns:
            Consent confirmation response
        """
        # Verify token in Redis
        token_data = await self.redis_client.get(f"consent:token:{token}")
        if not token_data:
            raise ValueError("Invalid or expired consent token")

        token_data = token_data if isinstance(token_data, dict) else __import__("json").loads(token_data)

        # Check expiry
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.utcnow() > expires_at:
            raise ValueError("Consent token has expired")

        # Find pending consent record
        record = await self.consent_repository.get_pending_by_token(token)
        if not record:
            raise ValueError("Consent record not found for token")

        # Confirm consent
        confirmed_at = datetime.utcnow()
        confirmed_record = await self.consent_repository.confirm_consent(
            record.id, confirmed_at
        )

        # Mark as active in Redis
        await self.redis_client.set_active_consent(record.user_id)

        # Clean up token
        await self.redis_client.delete(f"consent:token:{token}")

        logger.info(f"Consent confirmed for user {record.user_id}")

        # Calculate expiry (1 year from confirmation)
        expires_at = confirmed_at + timedelta(days=365)

        return {
            "consent_id": confirmed_record.id,
            "status": "active",
            "confirmed_at": confirmed_at,
            "expires_at": expires_at,
        }

    async def verify_active_consent(self, user_id: str) -> bool:
        """
        Check if user has active COPPA consent.

        Args:
            user_id: User ID to check

        Returns:
            True if user has active consent
        """
        # Check Redis first (fast path)
        has_consent = await self.redis_client.get_active_consent(user_id)
        if has_consent:
            return True

        # Fallback to database
        return await self.consent_repository.has_active_consent(user_id)

    async def get_consent_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get consent status for a user.

        Args:
            user_id: User ID

        Returns:
            Consent status response
        """
        records = await self.consent_repository.get_consent_status(user_id)

        consent_summary = []
        has_active = False

        for record in records:
            summary = {
                "consent_id": record.id,
                "consent_type": record.consent_type,
                "status": record.status,
                "initiated_at": record.created_at,
                "confirmed_at": record.consented_at,
                "expires_at": None,
            }

            # Parse expiry from metadata
            if record.metadata_json and "expires_at" in record.metadata_json:
                summary["expires_at"] = datetime.fromisoformat(
                    record.metadata_json["expires_at"]
                )

            if record.status == "granted":
                has_active = True

            consent_summary.append(summary)

        return {
            "has_active_consent": has_active,
            "consent_records": consent_summary,
        }

    async def revoke_consent(
        self, record_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Revoke a consent record.

        Args:
            record_id: Consent record ID

        Returns:
            Revoked consent record or None
        """
        record = await self.consent_repository.revoke_consent(record_id)

        if record:
            # Revoke in Redis
            await self.redis_client.revoke_active_consent(record.user_id)

            logger.info(f"Consent revoked for user {record.user_id}")

        return record

    def _mask_email(self, email: str) -> str:
        """
        Mask email address for privacy.

        Example: john.doe@gmail.com -> j***@gmail.com
        """
        if "@" not in email:
            return email

        local, domain = email.split("@")
        masked_local = local[0] + "***" if len(local) > 1 else local[0]
        return f"{masked_local}@{domain}"


# Singleton instance
_consent_service: Optional[ConsentService] = None


def get_consent_service() -> ConsentService:
    """Get singleton consent service instance."""
    global _consent_service
    if _consent_service is None:
        raise RuntimeError("ConsentService not initialized")
    return _consent_service


def initialize_consent_service(consent_repository: ConsentRepository) -> ConsentService:
    """
    Initialize and return consent service.

    Args:
        consent_repository: Consent repository instance

    Returns:
        Initialized ConsentService
    """
    global _consent_service
    _consent_service = ConsentService(consent_repository)
    return _consent_service
