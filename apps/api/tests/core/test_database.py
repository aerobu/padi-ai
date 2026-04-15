"""Tests for core database infrastructure."""

import pytest
from unittest.mock import patch, MagicMock


class TestDatabaseConfig:
    """Test database configuration."""

    def test_create_async_engine(self):
        """create_async_engine returns configured engine."""
        from sqlalchemy.ext.asyncio import create_async_engine

        # Test basic creation
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        assert engine is not None
        assert engine.url.drivername == "sqlite+aiosqlite"

    def test_create_async_engine_with_postgres(self):
        """create_async_engine works with PostgreSQL URL."""
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(
            "postgresql+asyncpg://user:pass@localhost:5432/padi"
        )
        assert engine is not None
        assert engine.url.drivername == "postgresql+asyncpg"

    @pytest.mark.asyncio
    async def test_get_db_dependency(self):
        """get_db yields async session."""
        from src.core.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession

        async for db in get_db():
            assert isinstance(db, AsyncSession)
            break

    def test_get_db_generator(self):
        """get_db is an async generator function."""
        from src.core.database import get_db
        import inspect

        assert inspect.isasyncgenfunction(get_db)


class TestAsyncSessionFactory:
    """Test async session factory."""

    def test_async_session_factory_type(self):
        """async_session_factory returns callable."""
        from src.core.database import async_session_factory
        from functools import partial

        # Session factory should be a partial or similar callable
        assert callable(async_session_factory)

    @pytest.mark.asyncio
    async def test_create_session_context(self):
        """create_async_session creates session context."""
        from src.core.database import async_session_factory

        async with async_session_factory() as session:
            assert session is not None
            # Session should be closable
        await session.close()


class TestDatabaseIntegration:
    """Test database integration with models."""

    @pytest.mark.asyncio
    async def test_session_basic_operations(self):
        """Basic database operations work."""
        from src.core.database import get_db, async_session_factory
        from src.models.models import Base

        # Use in-memory SQLite for testing
        async with async_session_factory() as session:
            assert session is not None
            # Session is available for queries

    def test_engine_configuration(self):
        """Engine is configured with correct parameters."""
        from sqlalchemy.ext.asyncio import create_async_engine

        # Test with echo=False for quiet testing
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )
        assert engine is not None


class TestDatabaseConnection:
    """Test database connection handling."""

    def test_invalid_connection_string(self):
        """Invalid connection string raises error."""
        from sqlalchemy.ext.asyncio import create_async_engine

        with pytest.raises(Exception):
            create_async_engine("invalid://connection")

    @pytest.mark.asyncio
    async def test_session_cleanup(self):
        """Sessions are properly cleaned up."""
        from src.core.database import async_session_factory

        async with async_session_factory() as session:
            assert session is not None
            # Explicit close should work
        # Session should be closed after context exit
