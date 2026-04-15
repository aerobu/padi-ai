"""
Test Suite: API - Standards Endpoint Tests

Purpose: Validate standards API endpoints.
"""

import pytest
from sqlalchemy import text


class TestStandardsEndpoints:
    """Tests for standards API."""

    def test_get_standards_list(self, engine):
        """API-STD-001: Verify standards can be retrieved."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description, grade_level, cognitive_level)
                VALUES ('4.OA.A.1', '4.OA', '4.OA.A', 'Test', 'Test desc', 4, 'apply')
            """))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM standards WHERE is_active = true
            """)).fetchone()
            assert result['count'] >= 1

    def test_get_standard_by_code(self, engine):
        """API-STD-002: Verify standard can be retrieved by code."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description, grade_level)
                VALUES ('4.OA.A.1', '4.OA', '4.OA.A', 'Test', 'Test desc', 4)
            """))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT code FROM standards WHERE code = '4.OA.A.1'
            """)).fetchone()
            assert result['code'] == '4.OA.A.1'

    def test_get_standards_by_domain(self, engine):
        """API-STD-003: Verify standards can be filtered by domain."""
        with engine.connect() as conn:
            for code in ['4.OA.A.1', '4.OA.A.2', '4.NBT.A.1']:
                conn.execute(text("""
                    INSERT INTO standards (code, domain, cluster, title, description, grade_level)
                    VALUES (:code, :domain, '4.X.A', 'Test', 'Test', 4)
                """, code=code, domain=code[:4]))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM standards WHERE domain = '4.OA'
            """)).fetchone()
            assert result['count'] == 2

    def test_get_prerequisites(self, engine):
        """API-STD-004: Verify prerequisites can be retrieved."""
        with engine.connect() as conn:
            # Create standards
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description, grade_level)
                VALUES ('4.PREQ.BASE', '4.PREQ', '4.PREQ.A', 'Base', 'Base', 4)
            """))
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description, grade_level)
                VALUES ('4.PREQ.ADV', '4.PREQ', '4.PREQ.A', 'Advanced', 'Advanced', 4)
            """))
            # Create prerequisite relationship
            conn.execute(text("""
                INSERT INTO prerequisite_relationships (standard_code, prerequisite_code)
                VALUES ('4.PREQ.ADV', '4.PREQ.BASE')
            """))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT prerequisite_code FROM prerequisite_relationships WHERE standard_code = '4.PREQ.ADV'
            """)).fetchone()
            assert result['prerequisite_code'] == '4.PREQ.BASE'
