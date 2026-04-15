"""
Database connection and session management.
"""

import logging
from typing import AsyncGenerator, Annotated
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DATABASE_POOL_MIN,
    max_overflow=settings.DATABASE_POOL_MAX - settings.DATABASE_POOL_MIN,
    connect_args={"options": "-c timezone=utc"},
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with proper cleanup.
    Usage: async with get_db_session() as db: ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# For FastAPI Depends - create a wrapper that returns a session without committing
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session.
    Does not commit - caller is responsible for commit/rollback.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# For services that need transaction control
async def get_db_with_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session with transaction control.
    Use when you need explicit commit/rollback within the service.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
