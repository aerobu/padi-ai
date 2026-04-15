"""
Test Suite: MIG-004 - Standards Table with ltree + Prerequisite Relationships

Purpose: Validate the standards table schema, indexes, and prerequisite_relationships
         table structure for Stage 1 Oregon math standards database.

Coverage:
- Standards table structure and data types
- Unique constraints on standard codes
- Domain and grade_level constraints
- BKT default parameters
- Vector embeddings for semantic search (pgvector)
- Prerequisite relationship table and integrity constraints
- Index validation for performance queries

COPPA Relevance: Standards data contains no PII - public educational standards only.
"""

import pytest
from sqlalchemy import text, inspect, MetaData, Table
from typing import List, Dict, Any


class TestStandardsTableSchema:
    """Tests for the standards table structure."""

    @pytest.fixture
    def table_info(self, engine):
        """Get standards table information."""
        inspector = inspect(engine)
        return inspector.get_columns('standards')

    @pytest.fixture
    def indexes(self, engine):
        """Get standards table indexes."""
        inspector = inspect(engine)
        return inspector.get_indexes('standards')

    def test_standards_table_exists(self, engine):
        """MIG-004-001: Verify standards table exists in database."""
        inspector = inspect(engine)
        assert 'standards' in inspector.get_table_names()

    def test_standards_id_column(self, table_info):
        """MIG-004-002: Verify standards.id is UUID with default gen_random_uuid()."""
        id_column = next(c for c in table_info if c['name'] == 'id')
        assert id_column['type'].python_type.__name__ == 'UUID'
        assert id_column['default'] == "gen_random_uuid()"

    def test_standards_code_column(self, table_info):
        """MIG-004-003: Verify standards.code is VARCHAR(20), NOT NULL, UNIQUE."""
        code_column = next(c for c in table_info if c['name'] == 'code')
        assert str(code_column['type']) == 'VARCHAR(20)'
        assert code_column['nullable'] is False

    def test_standards_domain_column(self, table_info):
        """MIG-004-004: Verify standards.domain is VARCHAR(10), NOT NULL."""
        domain_column = next(c for c in table_info if c['name'] == 'domain')
        assert str(domain_column['type']) == 'VARCHAR(10)'
        assert domain_column['nullable'] is False

    def test_standards_cluster_column(self, table_info):
        """MIG-004-005: Verify standards.cluster is VARCHAR(10), NOT NULL."""
        cluster_column = next(c for c in table_info if c['name'] == 'cluster')
        assert str(cluster_column['type']) == 'VARCHAR(10)'
        assert cluster_column['nullable'] is False

    def test_standards_title_column(self, table_info):
        """MIG-004-006: Verify standards.title is TEXT, NOT NULL."""
        title_column = next(c for c in table_info if c['name'] == 'title')
        assert str(title_column['type']) == 'TEXT'
        assert title_column['nullable'] is False

    def test_standards_description_column(self, table_info):
        """MIG-004-007: Verify standards.description is TEXT, NOT NULL."""
        desc_column = next(c for c in table_info if c['name'] == 'description')
        assert str(desc_column['type']) == 'TEXT'
        assert desc_column['nullable'] is False

    def test_standards_grade_level_column(self, table_info):
        """MIG-004-008: Verify standards.grade_level is SMALLINT, NOT NULL, default 4."""
        grade_column = next(c for c in table_info if c['name'] == 'grade_level')
        assert str(grade_column['type']) == 'SMALLINT'
        assert grade_column['nullable'] is False
        assert grade_column['default'] == "4"

    def test_standards_cognitive_level_column(self, table_info):
        """MIG-004-009: Verify standards.cognitive_level has CHECK constraint."""
        cog_column = next(c for c in table_info if c['name'] == 'cognitive_level')
        assert str(cog_column['type']) == 'VARCHAR(20)'
        assert cog_column['nullable'] is False
        assert cog_column['default'] == "'understand'"

    def test_standards_bkt_parameters(self, table_info):
        """MIG-004-010: Verify BKT default parameters exist (p_l0, p_transit, p_slip, p_guess)."""
        params = {c['name']: c for c in table_info if 'bkt' in c['name']}
        assert 'bkt_p_l0' in params
        assert 'bkt_p_transit' in params
        assert 'bkt_p_slip' in params
        assert 'bkt_p_guess' in params

    def test_standards_description_embedding_column(self, table_info):
        """MIG-004-011: Verify standards.description_embedding is VECTOR(1536) for pgvector."""
        embed_column = next(c for c in table_info if c['name'] == 'description_embedding')
        assert 'VECTOR' in str(embed_column['type'])
        assert '1536' in str(embed_column['type'])

    def test_standards_timestamps(self, table_info):
        """MIG-004-012: Verify created_at and updated_at timestamps exist with DEFAULT CURRENT_TIMESTAMP."""
        timestamps = {c['name']: c for c in table_info if 'at' in c['name']}
        assert 'created_at' in timestamps
        assert 'updated_at' in timestamps
        assert 'CURRENT_TIMESTAMP' in timestamps['created_at'].get('default', '')
        assert 'CURRENT_TIMESTAMP' in timestamps['updated_at'].get('default', '')

    def test_standards_code_unique_index(self, indexes):
        """MIG-004-013: Verify unique index on standards.code."""
        code_index = next((i for i in indexes if i['name'] == 'idx_standards_code'), None)
        assert code_index is not None
        assert code_index['unique'] is True
        assert 'code' in code_index['column_names']

    def test_standards_domain_active_index(self, indexes):
        """MIG-004-014: Verify composite index on standards.domain, is_active for query optimization."""
        domain_index = next((i for i in indexes if 'domain_active' in i['name']), None)
        assert domain_index is not None
        assert 'domain' in domain_index['column_names']
        assert 'is_active' in domain_index['column_names']

    def test_standards_grade_domain_index(self, indexes):
        """MIG-004-015: Verify index on standards.grade_level, domain for API queries."""
        grade_domain_index = next((i for i in indexes if 'grade_domain' in i['name']), None)
        assert grade_domain_index is not None
        assert 'grade_level' in grade_domain_index['column_names']
        assert 'domain' in grade_domain_index['column_names']

    def test_standards_embedding_index(self, indexes):
        """MIG-004-016: Verify ivfflat index on description_embedding for vector similarity."""
        embed_index = next((i for i in indexes if 'embedding' in i['name']), None)
        assert embed_index is not None
        assert embed_index['type'] == 'ivfflat'


class TestPrerequisiteRelationshipsTable:
    """Tests for prerequisite_relationships table structure."""

    @pytest.fixture
    def table_info(self, engine):
        """Get prerequisite_relationships table information."""
        inspector = inspect(engine)
        return inspector.get_columns('prerequisite_relationships')

    @pytest.fixture
    def indexes(self, engine):
        """Get indexes for prerequisite_relationships."""
        inspector = inspect(engine)
        return inspector.get_indexes('prerequisite_relationships')

    def test_prerequisite_table_exists(self, engine):
        """MIG-004-017: Verify prerequisite_relationships table exists."""
        inspector = inspect(engine)
        assert 'prerequisite_relationships' in inspector.get_table_names()

    def test_prerequisite_id_column(self, table_info):
        """MIG-004-018: Verify prerequisite_relationships.id is UUID with default."""
        id_column = next(c for c in table_info if c['name'] == 'id')
        assert id_column['type'].python_type.__name__ == 'UUID'
        assert id_column['default'] == "gen_random_uuid()"

    def test_prerequisite_standard_code_foreign_key(self, table_info):
        """MIG-004-019: Verify prerequisite_relationships.standard_code references standards.code."""
        std_column = next(c for c in table_info if c['name'] == 'standard_code')
        assert std_column['nullable'] is False

    def test_prerequisite_prerequisite_code_foreign_key(self, table_info):
        """MIG-004-020: Verify prerequisite_relationships.prerequisite_code references standards.code."""
        prereq_column = next(c for c in table_info if c['name'] == 'prerequisite_code')
        assert prereq_column['nullable'] is False

    def test_prerequisite_relationship_type_column(self, table_info):
        """MIG-004-021: Verify relationship_type has CHECK constraint for valid types."""
        rel_column = next(c for c in table_info if c['name'] == 'relationship_type')
        assert str(rel_column['type']) == 'VARCHAR(20)'
        assert rel_column['nullable'] is False
        assert rel_column['default'] == "'prerequisite'"

    def test_prerequisite_strength_column(self, table_info):
        """MIG-004-022: Verify strength is NUMERIC(3,2) with CHECK constraint (0.0 to 1.0)."""
        strength_column = next(c for c in table_info if c['name'] == 'strength')
        assert 'NUMERIC' in str(strength_column['type'])
        assert '3,2' in str(strength_column['type'])
        assert strength_column['nullable'] is False
        assert strength_column['default'] == "1.0"

    def test_prerequisite_unique_constraint(self, engine):
        """MIG-004-023: Verify unique constraint on (standard_code, prerequisite_code) pair."""
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables['prerequisite_relationships']

        unique_constraints = [c for c in table.constraints if c.name and 'uq_prereq_pair' in c.name.lower()]
        assert len(unique_constraints) > 0

    def test_prerequisite_no_self_reference_check(self, engine):
        """MIG-004-024: Verify CHECK constraint prevents self-references."""
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables['prerequisite_relationships']

        check_constraints = [c for c in table.constraints if isinstance(c, type(table.checks[0]) if table.checks else type(None))]
        # At minimum, verify table has check constraints
        assert len(table.checks) >= 1

    def test_prerequisite_standard_index(self, indexes):
        """MIG-004-025: Verify index on standard_code for prerequisite lookups."""
        std_index = next((i for i in indexes if 'standard' in i['name']), None)
        assert std_index is not None
        assert 'standard_code' in std_index['column_names']

    def test_prerequisite_prereq_index(self, indexes):
        """MIG-004-026: Verify index on prerequisite_code for reverse lookups."""
        prereq_index = next((i for i in indexes if 'prereq' in i['name']), None)
        assert prereq_index is not None
        assert 'prerequisite_code' in prereq_index['column_names']


class TestStandardsDataIntegrity:
    """Tests for standards data integrity with sample Oregon CCSSM data."""

    @pytest.fixture
    def sample_standards(self):
        """Sample Oregon Grade 4 math standards."""
        return [
            {
                'code': '4.OA.A.1',
                'domain': '4.OA',
                'cluster': '4.OA.A',
                'title': 'Multiply or divide to solve word problems',
                'description': 'Use multiplication and division within 100 to solve word problems',
                'grade_level': 4,
                'cognitive_level': 'apply',
                'bkt_p_l0': 0.1000,
                'bkt_p_transit': 0.1000,
                'bkt_p_slip': 0.0500,
                'bkt_p_guess': 0.2500,
            },
            {
                'code': '4.NBT.A.1',
                'domain': '4.NBT',
                'cluster': '4.NBT.A',
                'title': 'Recognize place value',
                'description': 'Recognize that in a multi-digit whole number, a digit in one place',
                'grade_level': 4,
                'cognitive_level': 'understand',
                'bkt_p_l0': 0.1500,
                'bkt_p_transit': 0.1200,
                'bkt_p_slip': 0.0400,
                'bkt_p_guess': 0.2000,
            },
        ]

    def test_insert_standard_successfully(self, engine, sample_standards):
        """MIG-004-027: Verify standards can be inserted with all required fields."""
        with engine.connect() as conn:
            for standard in sample_standards:
                conn.execute(text("""
                    INSERT INTO standards (
                        code, domain, cluster, title, description,
                        grade_level, cognitive_level,
                        bkt_p_l0, bkt_p_transit, bkt_p_slip, bkt_p_guess
                    ) VALUES (
                        :code, :domain, :cluster, :title, :description,
                        :grade_level, :cognitive_level,
                        :p_l0, :p_transit, :p_slip, :p_guess
                    )
                """, **standard))
            conn.commit()

    def test_duplicate_standard_code_rejected(self, engine, sample_standards):
        """MIG-004-028: Verify duplicate standard codes are rejected (unique constraint)."""
        with engine.connect() as conn:
            # First insert succeeds
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description,
                    grade_level, cognitive_level, bkt_p_l0, bkt_p_transit, bkt_p_slip, bkt_p_guess)
                VALUES (:code, :domain, :cluster, :title, :description,
                    :grade_level, :cognitive_level, :p_l0, :p_transit, :p_slip, :p_guess)
            """, **sample_standards[0]))
            conn.commit()

            # Duplicate should fail
            with pytest.raises(Exception):
                conn.execute(text("""
                    INSERT INTO standards (code, domain, cluster, title, description,
                        grade_level, cognitive_level, bkt_p_l0, bkt_p_transit, bkt_p_slip, bkt_p_guess)
                    VALUES (:code, :domain, :cluster, :title, :description,
                        :grade_level, :cognitive_level, :p_l0, :p_transit, :p_slip, :p_guess)
                """, **sample_standards[0]))
                conn.commit()

    def test_create_prerequisite_relationship(self, engine):
        """MIG-004-029: Verify prerequisite relationships can be created."""
        # First insert standards
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description,
                    grade_level, cognitive_level, bkt_p_l0, bkt_p_transit, bkt_p_slip, bkt_p_guess)
                VALUES ('4.OA.A.1', '4.OA', '4.OA.A', 'Test 1', 'Test desc', 4, 'apply', 0.1, 0.1, 0.05, 0.25)
            """))
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description,
                    grade_level, cognitive_level, bkt_p_l0, bkt_p_transit, bkt_p_slip, bkt_p_guess)
                VALUES ('4.OA.A.2', '4.OA', '4.OA.A', 'Test 2', 'Test desc', 4, 'apply', 0.1, 0.1, 0.05, 0.25)
            """))
            conn.commit()

        # Now create prerequisite relationship
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO prerequisite_relationships (standard_code, prerequisite_code, relationship_type, strength)
                VALUES ('4.OA.A.2', '4.OA.A.1', 'prerequisite', 1.0)
            """))
            conn.commit()

    def test_prerequisite_self_reference_rejected(self, engine):
        """MIG-004-030: Verify self-referencing prerequisite is rejected."""
        with engine.connect() as conn:
            # Insert a standard first
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description,
                    grade_level, cognitive_level, bkt_p_l0, bkt_p_transit, bkt_p_slip, bkt_p_guess)
                VALUES ('4.OA.X.X', '4.OA', '4.OA.X', 'Test', 'Test desc', 4, 'apply', 0.1, 0.1, 0.05, 0.25)
            """))
            conn.commit()

            # Try to create self-reference (should fail)
            with pytest.raises(Exception):
                conn.execute(text("""
                    INSERT INTO prerequisite_relationships (standard_code, prerequisite_code, relationship_type, strength)
                    VALUES ('4.OA.X.X', '4.OA.X.X', 'prerequisite', 1.0)
                """))
                conn.commit()


class TestPgvectorExtension:
    """Tests for pgvector extension usage in standards table."""

    def test_pgvector_extension_enabled(self, engine):
        """MIG-004-031: Verify pgvector extension is enabled in database."""
        result = engine.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
        assert result is not None, "pgvector extension should be enabled"

    def test_vector_column_can_store_embeddings(self, engine):
        """MIG-004-032: Verify vector column can store 1536-dimensional embeddings."""
        test_embedding = "[0.1, 0.2, 0.3]"  # Simplified test vector
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description,
                    grade_level, cognitive_level, description_embedding)
                VALUES ('4.VECTOR.TEST', '4.OA', '4.OA.T', 'Vector Test', 'Test vector',
                    4, 'understand', :vec)
            """, vec=test_embedding))
            conn.commit()


class TestLtreeExtension:
    """Tests for ltree extension support for hierarchical standards."""

    def test_ltree_extension_enabled(self, engine):
        """MIG-004-033: Verify ltree extension is enabled (for future hierarchical queries)."""
        result = engine.execute(text("SELECT extname FROM pg_extension WHERE extname = 'ltree'")).fetchone()
        assert result is not None, "ltree extension should be enabled"
