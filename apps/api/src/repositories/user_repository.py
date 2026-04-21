"""
User repository for data access.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User
from src.repositories.base import AsyncRepository


class UserRepository(AsyncRepository[User]):
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """Get user by Auth0 ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.auth0_id == auth0_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email_hash(self, email_hash: str) -> Optional[User]:
        """Get user by email hash."""
        result = await self.session.execute(
            select(self.model).where(self.model.email_hash == email_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_field(self, field: str, value: Any) -> Optional[User]:
        """Get user by arbitrary field."""
        statement = select(self.model).where(getattr(self.model, field) == value)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_users(
        self, role: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[User]:
        """List users with optional role filter."""
        statement = select(self.model).offset(offset).limit(limit)
        if role:
            statement = statement.where(self.model.role == role)
        statement = statement.order_by(self.model.created_at)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
