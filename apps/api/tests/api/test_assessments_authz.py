"""
Tests for ownership (IDOR) guard on POST /assessments.

Task 1.4 - Security remediation: verify that a parent cannot start an
assessment for a student they don't own, and that a bogus student_id
returns 404 rather than leaking any existence information.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from src.models.models import User, Student


@pytest.mark.asyncio
async def test_start_assessment_forbidden_for_non_owning_parent(
    client, async_db_session
):
    """A parent cannot start an assessment for another parent's student."""
    # Parent A owns Student X.
    # The `client` fixture JWT sub is "test-user-id" — different from "parent-a".
    parent_a = User(
        id="parent-a",
        auth0_id="auth0|a",
        role="parent",
        is_active=True,
        first_name="A",
        last_name="Parent",
    )
    parent_a.set_email("a@example.com")
    student_x = Student(
        id=str(uuid4()),
        parent_id="parent-a",
        grade_level=4,
        display_name="Child X",
        is_active=True,
    )
    async_db_session.add_all([parent_a, student_x])
    await async_db_session.flush()

    # The `client` fixture authenticates as "test-user-id" (NOT "parent-a"),
    # so the ownership check must reject this request with 403.
    response = await client.post(
        "/api/v1/assessments",
        json={"student_id": student_x.id, "assessment_type": "diagnostic"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_start_assessment_not_found_for_bogus_student(
    client, async_db_session
):
    """Bogus student_id returns 404, not 403 (which would confirm existence)."""
    response = await client.post(
        "/api/v1/assessments",
        json={"student_id": str(uuid4()), "assessment_type": "diagnostic"},
    )
    assert response.status_code == 404, response.text
