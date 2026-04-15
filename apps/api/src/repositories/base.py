"""
Base repository with common CRUD operations.
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Selectinload
from sqlalchemy.sql import ColumnElement

from src.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class AsyncRepository(Generic[ModelType]):
    """Base async repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """Get all records with pagination."""
        result = await self.session.execute(
            select(self.model)
            .offset(offset)
            .limit(limit)
            .order_by(self.model.created_at)
        )
        return list(result.scalars().all())

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        record = self.model(**data)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update(
        self, id: str, updates: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update an existing record."""
        statement = (
            update(self.model)
            .where(self.model.id == id)
            .values(updates)
            .returning(self.model)
        )
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, id: str) -> bool:
        """Delete a record by ID."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, id: str) -> bool:
        """Check if a record exists by ID."""
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        """Count total records."""
        from sqlalchemy import func

        result = await self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()
