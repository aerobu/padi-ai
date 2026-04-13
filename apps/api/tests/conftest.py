"""Pytest configuration and fixtures for PADI.AI API tests."""

import os
import sys
import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import asyncio
from httpx import AsyncClient

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.core.config import get_settings
from src.models.models import Base


# Override settings for testing
@pytest.fixture(autouse=True, scope="session")
def test_settings():
    """Override settings with test configuration."""
    os.environ["DATABASE_URL"] = "sqlite:///./test_padi.db"
    os.environ["AUTH0_SECRET"] = "test-secret"
    os.environ["AUTH0_BASE_URL"] = "http://test.local"
    os.environ["AUTH0_ISSUER_BASE_URL"] = "https://test.auth0.com"

    settings = get_settings()
    return settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    """Create database engine for tests."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test_padi.db")

    if database_url.startswith("sqlite"):
        # For SQLite, remove ./ prefix for file path
        db_path = database_url.replace("sqlite:///./", "")
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(database_url)

    return engine


@pytest.fixture(scope="session")
def test_engine(engine):
    """Create test engine with fresh database."""
    # Drop all tables and recreate
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return engine


@pytest.fixture
def session(test_engine):
    """Create database session for each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()

    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest_asyncio.fixture
async def async_client():
    """Create async HTTP client for API tests."""
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_jwt_validation():
    """Mock JWT validation for tests that don't need auth."""
    with patch("src.core.security.Auth0Manager.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "email_verified": True
        }
        yield mock_validate


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for tests."""
    with patch("src.clients.llm_client.litellm.completion") as mock_completion:
        mock_completion.return_value = {
            "choices": [{
                "message": {"content": "Test response"}
            }]
        }
        yield mock_completion


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "role": "parent"
    }


@pytest.fixture
def sample_student_data():
    """Sample student data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "grade": 4,
        "date_of_birth": "2016-05-15"
    }


@pytest.fixture
def sample_standard_data():
    """Sample standard data for testing."""
    return {
        "code": "NBT.A.1",
        "description": "Place value relationships",
        "grade_level": 4,
        "subject": "math"
    }


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "text": "What is 1234 rounded to the nearest hundred?",
        "type": "multiple_choice",
        "difficulty": 2,
        "standard_id": 1,
        "points": 1
    }


# Cleanup fixture - uses SQLite in-memory database which auto-clears
# No explicit cleanup needed as SQLite session is scoped per test
@pytest.fixture(autouse=True)
def cleanup_database(test_engine):
    """Clean up database after each test - SQLite auto-clears."""
    yield
    # SQLite in-memory databases are automatically cleared when connection closes
