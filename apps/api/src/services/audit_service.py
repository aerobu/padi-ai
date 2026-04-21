"""Audit logging service — records sensitive lifecycle events.

Per CLAUDE.md the repository pattern is preferred, but the audit log is write-only
and singular; creating a full repository just to call `db.add()` once is overkill.
We encapsulate the write behind AuditService so that endpoints have a clean seam.
"""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import AuditLog


class AuditService:
    """Record audit-log events for COPPA compliance trail."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(
        self,
        *,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditLog:
        """Append an audit row. Caller is responsible for flushing/committing."""
        entry = AuditLog(
            id=str(uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata,
        )
        self.db.add(entry)
        return entry
