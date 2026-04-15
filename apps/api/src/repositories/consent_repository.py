"""
Consent repository for COPPA consent management.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AsyncRepository
from src.models.models import ConsentRecord, ConsentStatus, ConsentType


class ConsentRepository(AsyncRepository[ConsentRecord]):
    """Repository for ConsentRecord model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ConsentRecord)

    async def get_active_consent_for_user(
        self, user_id: str
    ) -> Optional[ConsentRecord]:
        """Get active consent record for user."""
        result = await self.session.execute(
            select(ConsentRecord)
            .where(
                ConsentRecord.user_id == user_id,
                ConsentRecord.status == ConsentStatus.GRANTED,
            )
            .order_by(ConsentRecord.consented_at.desc())
        )
        return result.scalar_one_or_none()

    async def has_active_consent(self, user_id: str) -> bool:
        """Check if user has active COPPA consent."""
        result = await self.session.execute(
            select(ConsentRecord.id)
            .where(
                ConsentRecord.user_id == user_id,
                ConsentRecord.status == ConsentStatus.GRANTED,
                ConsentRecord.consented_at != None,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_pending_consent(
        self,
        user_id: str,
        student_id: str,
        consent_type: str,
        token: str,
        expires_at: datetime,
    ) -> ConsentRecord:
        """Create a pending consent record."""
        record = ConsentRecord(
            user_id=user_id,
            student_id=student_id,
            consent_type=consent_type,
            status=ConsentStatus.PENDING,
            metadata_json={"token": token, "expires_at": expires_at.isoformat()},
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def confirm_consent(
        self, record_id: str, confirmed_at: datetime
    ) -> Optional[ConsentRecord]:
        """Confirm a pending consent."""
        record = await self.get_by_id(record_id)
        if not record:
            return None

        if record.status != ConsentStatus.PENDING:
            raise ValueError("Only pending consents can be confirmed")

        record.status = ConsentStatus.GRANTED
        record.consented_at = confirmed_at

        # Set expiry to 1 year from confirmation
        record.metadata_json = record.metadata_json or {}
        record.metadata_json["expires_at"] = (
            confirmed_at + timedelta(days=365)
        ).isoformat()

        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_consent_status(self, user_id: str) -> List[ConsentRecord]:
        """Get all consent records for user."""
        result = await self.session.execute(
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .order_by(ConsentRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_consent(
        self, record_id: str
    ) -> Optional[ConsentRecord]:
        """Revoke a consent."""
        record = await self.get_by_id(record_id)
        if not record:
            return None

        record.status = ConsentStatus.REVOKED
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_pending_by_token(self, token: str) -> Optional[ConsentRecord]:
        """Get pending consent by token."""
        result = await self.session.execute(
            select(ConsentRecord)
            .where(
                ConsentRecord.status == ConsentStatus.PENDING,
                ConsentRecord.metadata_json["token"].as_string() == token,
            )
        )
        return result.scalar_one_or_none()
