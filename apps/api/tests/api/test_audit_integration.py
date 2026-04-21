"""Task 2.4: end-to-end audit-log integration.

Verifies that a successful sensitive action produces an audit row.
"""
import pytest
from sqlalchemy import select
from datetime import datetime, timezone

from src.models.models import AuditLog, User, ConsentRecord, ConsentStatus


@pytest.mark.asyncio
async def test_student_creation_writes_audit_row(client, async_db_session):
    """Creating a student records student.created in the audit log.

    The client fixture mocks JWT via Depends(verify_jwt) with sub='test-user-id'.
    We create a parent user + active consent record matching that sub so the
    students endpoint succeeds.
    """
    from uuid import uuid4

    # Create the parent user that matches the mocked JWT sub
    parent = User(
        id="test-user-id",
        auth0_id="auth0|test-user-id",
        first_name="Test",
        last_name="Parent",
        role="parent",
        is_active=True,
    )
    parent.set_email("testparent@example.com")
    async_db_session.add(parent)
    await async_db_session.flush()

    # Grant active consent so POST /students succeeds
    consent = ConsentRecord(
        id=str(uuid4()),
        user_id="test-user-id",
        student_id=None,
        consent_type="coppa_verifiable",
        status=ConsentStatus.GRANTED,
        consented_at=datetime.now(timezone.utc),
    )
    async_db_session.add(consent)
    await async_db_session.flush()

    response = await client.post(
        "/api/v1/students",
        json={
            "display_name": "Audit Child",
            "grade_level": 4,
        },
    )
    # Accept any success status — some handlers return 200, some 201
    assert response.status_code in (200, 201), response.text

    rows = (await async_db_session.execute(
        select(AuditLog).where(AuditLog.action == "student.created")
    )).scalars().all()
    assert len(rows) >= 1
    latest = rows[-1]
    assert latest.resource_type == "student"
    assert latest.resource_id is not None
    assert latest.user_id == "test-user-id"
