"""Unit test for AuditService."""
import pytest
from sqlalchemy import select
from src.services.audit_service import AuditService
from src.models.models import AuditLog, User


async def _create_user(session, user_id: str, email: str = "test@example.com") -> User:
    """Helper: insert a User row so FK on audit_log.user_id is satisfied."""
    user = User(
        id=user_id,
        auth0_id=f"auth0|{user_id}",
        first_name="Test",
        last_name="User",
        role="parent",
        is_active=True,
    )
    user.set_email(email)
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_audit_service_records_event(async_db_session):
    await _create_user(async_db_session, "u1", "u1@example.com")
    svc = AuditService(async_db_session)
    entry = await svc.record(
        user_id="u1",
        action="consent.granted",
        resource_type="consent",
        resource_id="c1",
        ip_address="10.0.0.1",
        user_agent="pytest",
        metadata={"foo": "bar"},
    )
    await async_db_session.flush()

    assert entry.id is not None
    rows = (await async_db_session.execute(select(AuditLog))).scalars().all()
    # Depending on other tests sharing the session, filter by action:
    granted = [r for r in rows if r.action == "consent.granted" and r.user_id == "u1"]
    assert len(granted) == 1
    assert granted[0].ip_address == "10.0.0.1"
    assert granted[0].user_agent == "pytest"
    assert granted[0].metadata_json == {"foo": "bar"}


@pytest.mark.asyncio
async def test_audit_service_accepts_minimal_args(async_db_session):
    await _create_user(async_db_session, "u2", "u2@example.com")
    svc = AuditService(async_db_session)
    await svc.record(
        user_id="u2",
        action="student.created",
        resource_type="student",
        resource_id="s1",
    )
    await async_db_session.flush()
    rows = (await async_db_session.execute(
        select(AuditLog).where(AuditLog.action == "student.created", AuditLog.user_id == "u2")
    )).scalars().all()
    assert len(rows) == 1
    assert rows[0].ip_address is None
    assert rows[0].user_agent is None
    assert rows[0].metadata_json is None
