"""Pytest configuration and fixtures for PADI.AI backend tests.

Covers:
- DB fixtures (async PostgreSQL/SQLite; sync SQLite for repositories)
- JWT mocking (parent, teacher, admin, different-user roles)
- HTTP clients (sync test client, async client with DB override)
- LLM mocking (litellm.completion patch)
- Redis mocking (InMemoryRedisClient)
- Data seeds (standards, students, assessments, skill states)
"""

import os
import asyncio
import pytest
import pytest_asyncio

from contextlib import asynccontextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from unittest.mock import MagicMock, patch, AsyncMock

from src.core.redis_client import InMemoryRedisClient
from src.main import app
from src.core.security import verify_jwt


# Global event loop for asyncio tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# REDIS FIXTURES
# ============================================================================


@pytest.fixture
def mock_redis_client():
    """Opt-in fixture providing InMemoryRedisClient (dict-backed, no autouse)."""
    from src.core.redis_client import get_redis_client as _get, _redis_client

    client = InMemoryRedisClient()
    with patch("src.core.redis_client._redis_client", client):
        yield client


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================


@pytest.fixture
async def async_client():
    """Raw AsyncClient without DB/JWT overrides."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _override_verify_jwt(claims: dict):
    """Create a verify_jwt override that returns fixed claims."""
    async def override(token: str = None):
        return claims
    return override


@pytest.fixture
async def auth_headers(client):
    """Headers with parent JWT (depends on client fixture)."""
    return {"Authorization": "Bearer fake-parent-token"}


@pytest.fixture
async def admin_auth_headers(client):
    """Headers with admin JWT (depends on client fixture)."""
    return {"Authorization": "Bearer fake-admin-token"}


@pytest.fixture
async def different_user_headers(client):
    """Headers with different-user JWT (depends on client fixture)."""
    return {"Authorization": "Bearer fake-other-user-token"}


@pytest.fixture
def mock_jwt_as_admin():
    """Override JWT to admin role."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-admin-id",
        "email": "admin@example.com",
        "email_verified": True,
        "role": "admin",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_as_user():
    """Override JWT to authenticated user (no role)."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-user-id",
        "email": "user@example.com",
        "email_verified": True,
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_validation():
    """Override JWT to any authed user."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-user-id",
        "email": "test@example.com",
        "email_verified": True,
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_as_parent():
    """Override JWT to parent role."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-parent-id",
        "email": "parent@example.com",
        "email_verified": True,
        "role": "parent",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_jwt_as_teacher():
    """Override JWT to teacher role."""
    app.dependency_overrides[verify_jwt] = _override_verify_jwt({
        "sub": "test-teacher-id",
        "email": "teacher@example.com",
        "email_verified": True,
        "role": "teacher",
    })
    yield
    app.dependency_overrides.pop(verify_jwt, None)


@pytest.fixture
def mock_llm_client():
    """Patch litellm.completion to return canned response."""
    with patch("litellm.completion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )
        yield mock_completion


# ============================================================================
# DATABASE FIXTURES (ASYNC)
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def async_db_engine():
    """Create async PostgreSQL/SQLite engine for each test."""
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test_padi.db")
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )

    async with engine.begin() as conn:
        from src.models.models import Base
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="function")
def engine():
    """Sync engine for tests that need raw SQL or sync execution."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test_padi.db")

    if database_url.startswith("sqlite"):
        db_path = database_url.replace("sqlite:///./", "")
        sync_url = f"sqlite:///{db_path}"
        engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    else:
        sync_url = database_url.replace("asyncpg", "psycopg2")
        engine = create_engine(sync_url)

    return engine


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
        autoflush=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def test_api_client(async_db_session):
    """Create sync TestClient with get_db overridden."""
    from fastapi.testclient import TestClient
    from src.core.db import get_db

    app.dependency_overrides[get_db] = lambda: async_db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def test_api_client_with_base_url():
    """Create sync TestClient without DB override."""
    from fastapi.testclient import TestClient
    return TestClient(app, base_url="http://test")


@pytest.fixture
def db_session(async_db_session):
    """Alias for async_db_session (for convenience)."""
    return async_db_session


@pytest_asyncio.fixture
async def client(async_db_session, mock_redis_client):
    """Create async HTTP client for Stage 2 tests."""
    from httpx import AsyncClient, ASGITransport

    async def _override_get_db():
        yield async_db_session

    from src.core.db import get_db
    app.dependency_overrides[get_db] = _override_get_db

    # Apply default JWT mocking for parent role ONLY if not already overridden
    had_override = verify_jwt in app.dependency_overrides
    if not had_override:
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
        if not had_override:
            app.dependency_overrides.pop(verify_jwt, None)


# ============================================================================
# REPOSITORY FIXTURES (SYNC)
# ============================================================================


@pytest.fixture
def standards_repo(db_session):
    """Create a standards repository for testing."""
    from src.repositories.standard_repository import StandardRepository
    return StandardRepository(db_session)


# ============================================================================
# SYNC DATABASE FIXTURES (for repositories)
# ============================================================================


@pytest.fixture
def session(engine):
    """Synchronous SQLite session for repository unit tests.

    Repository tests use sync session.add() / session.commit() patterns
    and do not need async. This fixture creates fresh tables per test.
    """
    from src.models.models import Base

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def user(session):
    """Create a test User for repository tests."""
    from src.models.models import User
    u = User(
        id="user-1",
        auth0_id="auth0|user_1",
        first_name="Test",
        last_name="User",
        role="parent",
        is_active=True,
    )
    u.set_email("test@example.com")
    session.add(u)
    session.commit()
    return u


@pytest.fixture
def student(session, user):
    """Create a test Student for repository tests."""
    from src.models.models import Student
    s = Student(
        id="student-1",
        parent_id=user.id,
        grade_level=4,
        display_name="Test Student",
        is_active=True,
    )
    session.add(s)
    session.commit()
    return s


@pytest.fixture
def student2(session, user):
    """Create a second test Student for repository tests."""
    from src.models.models import Student
    s = Student(
        id="student-2",
        parent_id=user.id,
        grade_level=4,
        display_name="Test Student 2",
        is_active=True,
    )
    session.add(s)
    session.commit()
    return s


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def test_parent_for_student(async_db_session):
    """Create a parent User for testing."""
    from src.models.models import User

    parent = User(
        id="test-parent-id",
        auth0_id="auth0|test_parent",
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
async def test_student_without_assessment(async_db_session, test_parent_for_student):
    """Create a test student with NO completed assessment."""
    from src.models.models import Student
    from uuid import uuid4

    student = Student(
        id=str(uuid4()),
        parent_id="test-parent-id",
        grade_level=4,
        display_name="Test Student Without Assessment",
        is_active=True,
    )
    async_db_session.add(student)
    await async_db_session.flush()
    return student


@pytest_asyncio.fixture
async def seed_grade_4_standards(async_db_session):
    """Seed three Grade 4 Standard rows."""
    from src.models.models import Standard

    standards = [
        Standard(
            id="4.NBT.A.1",
            standard_code="4.NBT.A.1",
            grade_level=4,
            domain="Number and Operations in Base Ten",
            title="Place Value Understanding",
            description="Recognize that in a multi-digit whole number, a digit in one place represents ten times what it represents in the place to its right.",
            is_active=True,
        ),
        Standard(
            id="4.NBT.B.5",
            standard_code="4.NBT.B.5",
            grade_level=4,
            domain="Number and Operations in Base Ten",
            title="Multi-Digit Multiplication",
            description="Multiply a whole number of up to four digits by a one-digit whole number.",
            is_active=True,
        ),
        Standard(
            id="4.OA.A.1",
            standard_code="4.OA.A.1",
            grade_level=4,
            domain="Operations and Algebraic Thinking",
            title="Multiplicative Comparison",
            description="Interpret a multiplication equation as a comparison.",
            is_active=True,
        ),
    ]
    async_db_session.add_all(standards)
    await async_db_session.flush()
    return standards


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
    )
    async_db_session.add(assessment)
    await async_db_session.flush()
    return assessment


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
        )
        db_session.add(state)
        skill_states.append(state)

    await db_session.flush()
    return skill_states


@pytest.fixture
def cleanup_database():
    """Session-scoped no-op; container handles cleanup."""
    yield
