"""
Tests for Standards API endpoints.
"""
import pytest
from uuid import uuid4
from src.models.models import Standard, PrerequisiteRelationship

@pytest.mark.asyncio
class TestStandardsEndpoints:
    """Tests for standards API."""

    async def test_list_standards(self, client, async_db_session):
        """API-STD-001: Verify standards can be retrieved via endpoint."""
        # Seed data
        std = Standard(
            id=str(uuid4()),
            standard_code="4.OA.A.1",
            domain="OA",
            grade_level=4,
            title="Test Title",
            description="Test Desc",
            is_active=True
        )
        async_db_session.add(std)
        await async_db_session.commit()
        
        response = await client.get("/api/v1/standards?grade=4")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(s["code"] == "4.OA.A.1" for s in data["standards"])

    async def test_get_standard_by_code(self, client, async_db_session):
        """API-STD-002: Verify standard can be retrieved by code."""
        # Seed data
        std = Standard(
            id=str(uuid4()),
            standard_code="4.NBT.B.5",
            domain="NBT",
            grade_level=4,
            title="Multiplication",
            description="Desc",
            is_active=True
        )
        async_db_session.add(std)
        await async_db_session.commit()
        
        response = await client.get("/api/v1/standards/4.NBT.B.5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "4.NBT.B.5"
        assert data["domain"] == "NBT"

    async def test_get_standards_by_domain(self, client, async_db_session):
        """API-STD-003: Verify standards can be filtered by domain."""
        # Seed multiple standards
        async_db_session.add_all([
            Standard(id=str(uuid4()), standard_code="4.OA.A.1", domain="OA", grade_level=4, title="T1", description="D1"),
            Standard(id=str(uuid4()), standard_code="4.OA.A.2", domain="OA", grade_level=4, title="T2", description="D2"),
            Standard(id=str(uuid4()), standard_code="4.NBT.A.1", domain="NBT", grade_level=4, title="T3", description="D3")
        ])
        await async_db_session.commit()
        
        response = await client.get("/api/v1/standards?grade=4&domain=OA")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(s["domain"] == "OA" for s in data["standards"])

    async def test_get_standard_prerequisites(self, client, async_db_session):
        """API-STD-004: Verify prerequisites are returned in detail view."""
        # Seed standards
        base_id = str(uuid4())
        adv_id = str(uuid4())
        base = Standard(id=base_id, standard_code="3.OA.A.1", domain="OA", grade_level=3, title="Base", description="D")
        adv = Standard(id=adv_id, standard_code="4.OA.A.1", domain="OA", grade_level=4, title="Adv", description="D")
        async_db_session.add_all([base, adv])
        await async_db_session.flush()
        
        # Seed relationship
        rel = PrerequisiteRelationship(
            id=str(uuid4()),
            standard_id=adv_id,
            prerequisite_id=base_id,
            strength="required"
        )
        async_db_session.add(rel)
        await async_db_session.commit()
        
        response = await client.get("/api/v1/standards/4.OA.A.1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prerequisites"]) == 1
        assert data["prerequisites"][0]["prerequisite_code"] == "3.OA.A.1"

    async def test_get_standard_not_found(self, client):
        """API-STD-005: Verify 404 for non-existent standard."""
        response = await client.get("/api/v1/standards/9.9.9")
        assert response.status_code == 404
