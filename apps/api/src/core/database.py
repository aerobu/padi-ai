"""
Database connection and session management.
"""

import logging
from typing import AsyncGenerator, Annotated
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()

# Lazy engine creation
_engine = None
_async_session_factory = None


def get_engine():
    """Get or create the async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _settings.DATABASE_URL,
            echo=_settings.DEBUG,
            poolclass=NullPool,
            connect_args={"options": "-c timezone=utc"},
        )
    return _engine


def get_session_factory():
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _engine = get_engine()
        _async_session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with proper cleanup.
    Usage: async with get_db_session() as db: ...
    """
    async with get_session_factory() as session:
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
    session_factory = get_session_factory()
    async with session_factory() as session:
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
    async with get_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
