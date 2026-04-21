"""Pytest configuration and fixtures for PADI.AI API tests."""

import os
import sys

# ---------------------------------------------------------------------------
# Inject required secrets before any src.core.config import is reached.
# Use setdefault so CI/CD can override by exporting real values.
# ---------------------------------------------------------------------------
os.environ.setdefault(
    "ENCRYPTION_KEY_PASSPHRASE",
    "test-passphrase-32-characters-long-ok",  # 38 chars — satisfies min_length=32
)

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
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import testcontainers for PostgreSQL
try:
    from testcontainers.postgres import PostgresContainer
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False

# Global container reference
_container = None

# Configure test database URL BEFORE importing app
if TESTCONTAINERS_AVAILABLE:
    # Start PostgreSQL container
    _container = PostgresContainer("postgres:17", driver="asyncpg")
    _container.start()
    db_url = _container.get_connection_url().replace("psycopg2", "asyncpg")
else:
    # Fallback to SQLite
    db_url = "sqlite:///./test_padi.db"

os.environ["DATABASE_URL"] = db_url
os.environ["AUTH0_SECRET"] = "test-secret"
os.environ["AUTH0_BASE_URL"] = "http://test.local"
os.environ["AUTH0_ISSUER_BASE_URL"] = "https://test.auth0.com"

from src.main import app
from src.core.config import get_settings
from src.models.models import Base
from src.core.security import verify_jwt
from src.core.database import get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()



@pytest_asyncio.fixture
async def async_client():
    """Create async HTTP client for API tests."""
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Create auth headers for API tests and install verify_jwt override."""
    from src.main import app
    from src.core.security import verify_jwt
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-parent-id",
        "email": "p@example.com",
        "email_verified": True,
        "role": "parent",
    })
    yield {"Authorization": "Bearer test-token"}
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def admin_auth_headers():
    """Create auth headers with admin role and install verify_jwt override."""
    from src.main import app
    from src.core.security import verify_jwt
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "admin-user-id",
        "email": "admin@example.com",
        "email_verified": True,
        "role": "admin",
    })
    yield {"Authorization": "Bearer admin-token"}
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def different_user_headers():
    """Create auth headers for a different user and install verify_jwt override."""
    from src.main import app
    from src.core.security import verify_jwt
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "other-user-id",
        "email": "other@example.com",
        "email_verified": True,
        "role": "parent",
    })
    yield {"Authorization": "Bearer other-token"}
    app.dependency_overrides.pop(verify_jwt, None)


def _override_verify_jwt(payload: dict):
    """Return an async callable suitable for app.dependency_overrides[verify_jwt]."""
    async def _mock_verify_jwt():
        return payload
    return _mock_verify_jwt


@pytest.fixture
def mock_jwt_as_admin():
    """Override verify_jwt dependency to return an admin user payload."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "admin-user-id",
        "email": "admin@example.com",
        "email_verified": True,
        "role": "admin",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_as_user():
    """Override verify_jwt dependency to return a regular user payload."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-user-id",
        "email": "test@example.com",
        "email_verified": True,
        "role": "parent",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_validation():
    """Override verify_jwt dependency for tests that need any authed user."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-user-id",
        "email": "test@example.com",
        "email_verified": True,
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


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
        "code": "4.NBT.A.1",
        "description": "Place value relationships",
        "grade_level": 4,
        "subject": "math"
    }


# ==========================================================================
# Async SQLite Fixtures for API Tests
# ==========================================================================

@pytest_asyncio.fixture(scope="function")
async def async_db_engine():
    """
    Create async PostgreSQL engine for API tests.
    Uses testcontainers PostgreSQL for full feature compatibility.
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test_padi.db")

    # Replace psycopg2 with asyncpg for async operations
    async_db_url = database_url.replace("psycopg2", "asyncpg")
    engine = create_async_engine(async_db_url, echo=False)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_db_session(async_db_engine):
    """
    Create async database session for API tests.
    Creates fresh tables before each test, drops after.
    """
    async_session = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Drop and recreate tables for fresh state
    async with async_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session = async_session()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="function")
def test_api_client():
    """Create TestClient with get_db overridden.

    Yields a tuple of (client, sync_engine) so tests can write data
    before making requests using the sync engine directly.
    """
    from starlette.testclient import TestClient
    import asyncio
    import os

    database_url = os.getenv("DATABASE_URL", "sqlite:///./test_padi.db")

    # Use sync engine for test data writes (outside TestClient)
    if database_url.startswith("sqlite"):
        db_path = database_url.replace("sqlite:///./", "")
        sync_engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False}
        )
    else:
        sync_engine = create_engine(database_url.replace("asyncpg", "psycopg2"))

    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)

    # Use async engine for TestClient (FastAPI endpoints are async)
    async_db_url = database_url.replace("psycopg2", "asyncpg")
    async_engine = create_async_engine(async_db_url, echo=False)

    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    def cleanup():
        app.dependency_overrides.pop(get_db, None)
        sync_engine.dispose()
        # Run the async dispose in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(async_engine.dispose())
        finally:
            loop.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client, sync_engine
    finally:
        cleanup()


@pytest.fixture
def test_api_client_with_base_url():
    """Create TestClient with base_url='http://test' for parent dashboard tests."""
    from starlette.testclient import TestClient
    from unittest.mock import AsyncMock

    async def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)



@pytest.fixture
def mock_jwt_as_parent():
    """Override verify_jwt dependency to return a parent user payload.

    Uses 'parent-1' as sub to match test data, but can be overridden per-test
    if needed by setting APPARENT_PARENT_ID environment variable.
    """
    import os
    sub_id = os.getenv("APPARENT_PARENT_ID", "parent-1")
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": sub_id,
        "email": "parent@example.com",
        "email_verified": True,
        "role": "parent",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_as_teacher():
    """Override verify_jwt dependency to return a teacher user payload."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "teacher-1",
        "email": "teacher@example.com",
        "email_verified": True,
        "role": "teacher",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "text": "What is 1234 rounded to the nearest hundred?",
        "type": "multiple_choice",
        "difficulty": 2,
        "standard_id": "1",
        "points": 1
    }


# Cleanup fixture - uses PostgreSQL which we manage via testcontainers
@pytest.fixture(autouse=True, scope="session")
def cleanup_database():
    """Clean up database after tests."""
    yield
    # PostgreSQL container handles cleanup on session end


# === Test Data Fixtures for Stage 2 ===

@pytest_asyncio.fixture(scope="function")
async def db_session(async_db_session):
    """Provide async db session for Stage 2 tests."""
    yield async_db_session


@pytest_asyncio.fixture
async def test_parent_for_student(async_db_session):
    """Create a test parent for test_student."""
    from src.models.models import User

    parent = User(
        id="test-parent-id",
        auth0_id="auth0|test_parent_for_student",
        first_name="Test",
        last_name="Parent",
        role="parent",
        is_active=True,
    )
    parent.set_email("testparent@example.com")
    async_db_session.add(parent)
    await async_db_session.flush()
    return parent


@pytest_asyncio.fixture
async def test_student(async_db_session, test_parent_for_student):
    """Create a test student."""
    from src.models.models import Student
    from uuid import uuid4

    student = Student(
        id=str(uuid4()),
        parent_id="test-parent-id",
        grade_level=4,
        display_name="Test Student",
        is_active=True,
    )
    async_db_session.add(student)
    await async_db_session.flush()
    return student


@pytest_asyncio.fixture
async def test_assessment(async_db_session, test_student):
    """Create a test assessment."""
    from src.models.models import Assessment, AssessmentType, AssessmentStatus
    from uuid import uuid4
    from datetime import datetime

    assessment = Assessment(
        id=str(uuid4()),
        student_id=test_student.id,
        assessment_type=AssessmentType.DIAGNOSTIC.value,
        status=AssessmentStatus.COMPLETED.value,
        total_score=7.5,
        max_score=10.0,
        created_at=datetime.utcnow(),
    )
    async_db_session.add(assessment)
    await async_db_session.flush()
    return assessment


@pytest_asyncio.fixture
async def client(async_db_session):
    """Create async HTTP client for Stage 2 tests using ASGITransport.

    This fixture applies default JWT mocking (parent role) for Stage 2 tests.
    Tests requiring different JWT payloads should override with mock_jwt_as_* fixtures.
    """
    from httpx import AsyncClient, ASGITransport

    async def _override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = _override_get_db
    # Apply default JWT mocking for parent role
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-parent-id",
        "email": "test@example.com",
        "email_verified": True,
        "role": "parent",
    })
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def standards_repo(db_session):
    """Create a standards repository for testing."""
    from src.repositories.standard_repository import StandardRepository
    return StandardRepository(db_session)


@pytest.fixture
async def mock_skill_states_below_par(db_session, test_student):
    """Create mock skill states with Below Par proficiency."""
    from src.models.models import StudentSkillState
    from uuid import uuid4
    import random

    standards = ["3.OA.C.7", "4.NBT.B.5", "4.OA.A.1", "4.NF.A.1"]
    skill_states = []

    for std in standards:
        state = StudentSkillState(
            id=str(uuid4()),
            student_id=test_student.id,
            standard_id=std,
            mastery_prob=random.uniform(0.1, 0.4),
            proficiency_level="Below Par",
        )
        db_session.add(state)
        skill_states.append(state)

    await db_session.flush()
    return skill_states


@pytest.fixture
async def mock_skill_states_above_par(db_session, test_student):
    """Create mock skill states with Above Par proficiency."""
    from src.models.models import StudentSkillState
    from uuid import uuid4
    import random

    standards = ["3.OA.C.7", "4.NBT.B.5", "4.OA.A.1", "4.NF.A.1"]
    skill_states = []

    for std in standards:
        state = StudentSkillState(
            id=str(uuid4()),
            student_id=test_student.id,
            standard_id=std,
            mastery_prob=random.uniform(0.80, 0.95),
            proficiency_level="Above Par",
        )
        db_session.add(state)
        skill_states.append(state)

    await db_session.flush()
    return skill_states


@pytest.fixture
async def mock_skill_states_on_track(db_session, test_student):
    """Create mock skill states with On Track proficiency."""
    from src.models.models import StudentSkillState
    from uuid import uuid4
    import random

    standards = ["3.OA.C.7", "4.NBT.B.5", "4.OA.A.1", "4.NF.A.1"]
    skill_states = []

    for std in standards:
        state = StudentSkillState(
            id=str(uuid4()),
            student_id=test_student.id,
            standard_id=std,
            mastery_prob=random.uniform(0.45, 0.75),
            proficiency_level="On Par",
        )
        db_session.add(state)
        skill_states.append(state)

    await db_session.flush()
    return skill_states
