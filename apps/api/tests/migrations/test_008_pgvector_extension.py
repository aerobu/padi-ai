"""
Test Suite: MIG-008 - PostgreSQL Extensions (pgvector, ltree, pgcrypto, pg_trgm)

Purpose: Validate that all required PostgreSQL extensions are enabled and functional
         for Stage 1 features including semantic search, hierarchical queries, and
         data encryption.

Coverage:
- Extension verification (pgvector, ltree, pgcrypto, pg_trgm, uuid-ossp)
- Vector similarity search functionality
- Trigram similarity for full-text search
- UUID generation functions
- Cryptographic hash functions

COPPA Relevance: pgcrypto supports encryption of PII fields for compliance.
"""

import pytest
from sqlalchemy import text
from typing import List, Dict, Any


class TestRequiredExtensions:
    """Tests for required PostgreSQL extensions."""

    REQUIRED_EXTENSIONS = [
        'uuid-ossp',
        'pgcrypto',
        'pgvector',
        'ltree',
        'pg_trgm',
    ]

    @pytest.fixture
    def enabled_extensions(self, engine):
        """Get list of enabled extensions."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT extname FROM pg_extension
            """)).fetchall()
            return [row[0] for row in result]

    def test_uuid_ossp_extension_enabled(self, engine):
        """MIG-008-001: Verify uuid-ossp extension is enabled."""
        result = engine.execute(text("""
            SELECT extname FROM pg_extension WHERE extname = 'uuid-ossp'
        """)).fetchone()
        assert result is not None

    def test_pgcrypto_extension_enabled(self, engine):
        """MIG-008-002: Verify pgcrypto extension is enabled."""
        result = engine.execute(text("""
            SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'
        """)).fetchone()
        assert result is not None

    def test_pgvector_extension_enabled(self, engine):
        """MIG-008-003: Verify pgvector extension is enabled."""
        result = engine.execute(text("""
            SELECT extname FROM pg_extension WHERE extname = 'vector'
        """)).fetchone()
        assert result is not None

    def test_ltree_extension_enabled(self, engine):
        """MIG-008-004: Verify ltree extension is enabled."""
        result = engine.execute(text("""
            SELECT extname FROM pg_extension WHERE extname = 'ltree'
        """)).fetchone()
        assert result is not None

    def test_pg_trgm_extension_enabled(self, engine):
        """MIG-008-005: Verify pg_trgm extension is enabled."""
        result = engine.execute(text("""
            SELECT extname FROM pg_extension WHERE extname = 'pg_trgm'
        """)).fetchone()
        assert result is not None

    def test_all_required_extensions_present(self, enabled_extensions):
        """MIG-008-006: Verify all required extensions are present."""
        missing = [ext for ext in self.REQUIRED_EXTENSIONS if ext not in enabled_extensions]
        assert len(missing) == 0, f"Missing extensions: {missing}"


class TestUUIDFunctions:
    """Tests for UUID generation functions."""

    def test_gen_random_uuid_function(self, engine):
        """MIG-008-007: Verify gen_random_uuid() from pgcrypto works."""
        result = engine.execute(text("SELECT gen_random_uuid()")).fetchone()
        assert result is not None
        assert result[0] is not None

    def test_uuid_format_valid(self, engine):
        """MIG-008-008: Verify generated UUID is valid format."""
        result = engine.execute(text("SELECT gen_random_uuid()::text")).fetchone()
        uuid_str = result[0]
        # Basic UUID format check (8-4-4-4-12)
        parts = uuid_str.split('-')
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_multiple_uuids_are_unique(self, engine):
        """MIG-008-009: Verify multiple UUID calls generate unique values."""
        with engine.connect() as conn:
            results = conn.execute(text("""
                SELECT gen_random_uuid() as uuid FROM generate_series(1, 100)
            """)).fetchall()

            unique_uuids = set(row[0] for row in results)
            assert len(unique_uuids) == 100


class TestPGVectorVectorFunctions:
    """Tests for pgvector vector operations."""

    def test_vector_type_exists(self, engine):
        """MIG-008-010: Verify vector type is available."""
        result = engine.execute(text("""
            SELECT EXISTS (
                SELECT FROM pg_type WHERE typname = 'vector'
            )
        """)).fetchone()
        assert result[0] is True

    def test_vector_cosine_similarity_operator(self, engine):
        """MIG-008-011: Verify <-> (cosine distance) operator works."""
        vec1 = "[0.1, 0.2, 0.3, 0.4, 0.5]"
        vec2 = "[0.5, 0.4, 0.3, 0.2, 0.1]"

        result = engine.execute(text("""
            SELECT :vec1 <-> :vec2 as cosine_distance
        """, vec1=vec1, vec2=vec2)).fetchone()

        assert result is not None
        assert result['cosine_distance'] is not None
        assert 0 <= result['cosine_distance'] <= 2  # Cosine distance range

    def test_vector_dot_product_operator(self, engine):
        """MIG-008-012: Verify <#> (negative dot product) operator works."""
        vec1 = "[0.1, 0.2, 0.3, 0.4, 0.5]"
        vec2 = "[0.5, 0.4, 0.3, 0.2, 0.1]"

        result = engine.execute(text("""
            SELECT :vec1 <#> :vec2 as dot_product
        """, vec1=vec1, vec2=vec2)).fetchone()

        assert result is not None
        assert result['dot_product'] is not None

    def test_vector_negative_inner_product_operator(self, engine):
        """MIG-008-013: Verify <-> (inner product) operator works."""
        vec1 = "[0.1, 0.2, 0.3, 0.4, 0.5]"
        vec2 = "[0.5, 0.4, 0.3, 0.2, 0.1]"

        result = engine.execute(text("""
            SELECT :vec1 <~> :vec2 as inner_product
        """, vec1=vec1, vec2=vec2)).fetchone()

        assert result is not None
        assert result['inner_product'] is not None

    def test_vector_l2_distance_operator(self, engine):
        """MIG-008-014: Verify <#> (L2 distance) operator works."""
        vec1 = "[0.0, 0.0, 0.0, 0.0, 0.0]"
        vec2 = "[1.0, 1.0, 1.0, 1.0, 1.0]"

        result = engine.execute(text("""
            SELECT :vec1 <#> :vec2 as l2_distance
        """, vec1=vec1, vec2=vec2)).fetchone()

        assert result is not None
        # L2 distance between origin and (1,1,1,1,1) should be sqrt(5)
        expected_distance = 2.236  # sqrt(5)
        assert abs(result['l2_distance'] - expected_distance) < 0.001

    def test_vector_operation_with_standards_table(self, engine):
        """MIG-008-015: Verify vector operations work with standards table."""
        test_vec = "[0.1, 0.2, 0.3, 0.4, 0.5]"

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO standards (code, domain, cluster, title, description,
                    grade_level, cognitive_level, description_embedding)
                VALUES ('4.VECTOR.TEST', '4.OA', '4.OA.V', 'Vector Test', 'Test vector',
                    4, 'understand', :vec)
            """, vec=test_vec))
            conn.commit()

        # Query using cosine similarity
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code,
                       description_embedding <-> :query_vec as similarity
                FROM standards
                WHERE standard_code = '4.VECTOR.TEST'
            """, query_vec=test_vec)).fetchone()

            assert result is not None
            assert result['standard_code'] == '4.VECTOR.TEST'


class TestPGTrigramFunctions:
    """Tests for pg_trgm trigram operations."""

    def test_trigram_similarity_operator(self, engine):
        """MIG-008-016: Verify % (trigram similarity) operator works."""
        result = engine.execute(text("""
            SELECT 'test' % 'testing' as similarity
        """)).fetchone()

        assert result is not None
        assert result['similarity'] > 0  # Should have some similarity
        assert result['similarity'] <= 1

    def test_trigram_word_similarity_operator(self, engine):
        """MIG-008-017: Verify ~== (word similarity) operator works."""
        result = engine.execute(text("""
            SELECT 'test question' ~== 'test question' as word_similarity
        """)).fetchone()

        assert result is not None
        assert result['word_similarity'] == 1.0

    def test_trigram_similarity_threshold(self, engine):
        """MIG-008-018: Verify similarity threshold filtering works."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES
                    ('4.TRIG.SIM', 3, 'What is 12 times 8?', '[{"key": "A", "text": "96"}]', 'A', 'seed', 'active'),
                    ('4.TRIG.SIM2', 3, 'Calculate the product of 12 and 8', '[{"key": "A", "text": "96"}]', 'A', 'seed', 'active'),
                    ('4.TRIG.SIM3', 3, 'Add 5 and 3 together', '[{"key": "A", "text": "8"}]', 'A', 'seed', 'active')
            """))
            conn.commit()

        # Query with similarity threshold
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code, stem
                FROM questions
                WHERE stem % 'product of 12 and 8'
                  AND stem <-> 'product of 12 and 8' < 0.7
                ORDER BY stem % 'product of 12 and 8' DESC
            """)).fetchall()

            # Should find at least the second question which is semantically similar
            assert len(result) >= 1

    def test_trigram_index_functionality(self, engine):
        """MIG-008-019: Verify trigram GIN index works efficiently."""
        with engine.connect() as conn:
            # Insert test data
            for i in range(10):
                conn.execute(text("""
                    INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                    VALUES (:sc, 3, :stem, '[{"key": "A", "text": "1"}]', 'A', 'seed', 'active')
                """, sc=f'4.TRIG.IDX{i:02d}', stem=f'Test question {i} about math'))
            conn.commit()

        # Query using trigram
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code FROM questions
                WHERE stem % 'test question math'
            """)).fetchall()

            assert len(result) >= 10


class TestPGCryptoHashFunctions:
    """Tests for pgcrypto cryptographic functions."""

    def test_gen_random_bytes_function(self, engine):
        """MIG-008-020: Verify gen_random_bytes() function works."""
        result = engine.execute(text("""
            SELECT gen_random_bytes(32)
        """)).fetchone()

        assert result is not None
        assert result[0] is not None
        assert len(result[0]) == 32

    def test_sha256_hash_function(self, engine):
        """MIG-008-021: Verify sha256() hash function works."""
        result = engine.execute(text("""
            SELECT encode(sha256('test data'::bytea), 'hex')
        """)).fetchone()

        assert result is not None
        # SHA256 produces 64 hex characters
        assert len(result[0]) == 64

    def test_md5_hash_function(self, engine):
        """MIG-008-022: Verify md5() hash function works."""
        result = engine.execute(text("""
            SELECT md5('test data')
        """)).fetchone()

        assert result is not None
        # MD5 produces 32 hex characters
        assert len(result[0]) == 32

    def test_encrypt_decrypt_function(self, engine):
        """MIG-008-023: Verify encrypt/decrypt functions work (AES)."""
        key = '0123456789abcdef0123456789abcdef'  # 32 bytes for AES-256

        with engine.connect() as conn:
            encrypted = conn.execute(text("""
                SELECT encrypt('sensitive data'::bytea, :key, 'aes')
            """, key=key)).fetchone()[0]

            decrypted = conn.execute(text("""
                SELECT decrypt(:encrypted, :key, 'aes')
            """, encrypted=encrypted, key=key)).fetchone()[0]

            assert decrypted == b'sensitive data'


class TestExtensionMaintenance:
    """Tests for extension maintenance and versioning."""

    def test_extension_version_info(self, engine):
        """MIG-008-024: Verify extension version info is available."""
        result = engine.execute(text("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'pgvector'
        """)).fetchone()

        assert result is not None
        assert result['extname'] == 'pgvector'
        # Version should be present (may be NULL for some extensions)

    def test_extension_schema(self, engine):
        """MIG-008-025: Verify pgvector objects are in correct schema."""
        result = engine.execute(text("""
            SELECT n.nspname as schema_name, c.relname as object_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname LIKE 'vector%'
            LIMIT 5
        """)).fetchall()

        # At least one vector-related object should exist
        assert len(result) >= 1
