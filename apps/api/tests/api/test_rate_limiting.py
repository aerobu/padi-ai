"""
Tests for rate limiting logic.
"""
import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limiting_health(client: AsyncClient):
    """Verify that hitting the health endpoint too many times triggers a 429."""
    # The health endpoint doesn't have a limit applied in main.py yet, 
    # but the start_assessment does (10/minute).
    # Let's test start_assessment which has @limiter.limit("10/minute")
    
    # We'll try to hit it 15 times quickly.
    responses = []
    for _ in range(12):
        response = await client.post(
            "/api/v1/assessments",
            json={"student_id": "non-existent", "assessment_type": "diagnostic"}
        )
        responses.append(response.status_code)
    
    assert 429 in responses
