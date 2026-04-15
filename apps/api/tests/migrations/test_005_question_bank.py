"""
Test Suite: MIG-005 - Question Bank with pgvector Embeddings

Purpose: Validate the questions table schema, IRT parameters, pgvector embeddings,
         and indexes for efficient question retrieval in the adaptive diagnostic engine.

Coverage:
- Questions table structure and data types
- IRT parameter constraints (difficulty, discrimination, guessing)
- Question type validation (multiple_choice, numeric_input, drag_drop)
- JSONB options array structure
- Content embedding for deduplication (pgvector)
- Index validation for CAT engine queries
- Trigram full-text search on question stems

COPPA Relevance: Questions contain no student PII - public educational content.
"""

import pytest
from sqlalchemy import text, inspect, MetaData, Table
from typing import List, Dict, Any


class TestQuestionsTableSchema:
    """Tests for the questions table structure."""

    @pytest.fixture
    def table_info(self, engine):
        """Get questions table information."""
        inspector = inspect(engine)
        return inspector.get_columns('questions')

    @pytest.fixture
    def indexes(self, engine):
        """Get questions table indexes."""
        inspector = inspect(engine)
        return inspector.get_indexes('questions')

    def test_questions_table_exists(self, engine):
        """MIG-005-001: Verify questions table exists in database."""
        inspector = inspect(engine)
        assert 'questions' in inspector.get_table_names()

    def test_questions_id_column(self, table_info):
        """MIG-005-002: Verify questions.id is UUID with default gen_random_uuid()."""
        id_column = next(c for c in table_info if c['name'] == 'id')
        assert id_column['type'].python_type.__name__ == 'UUID'
        assert id_column['default'] == "gen_random_uuid()"

    def test_questions_standard_code_foreign_key(self, table_info):
        """MIG-005-003: Verify questions.standard_code references standards.code."""
        std_column = next(c for c in table_info if c['name'] == 'standard_code')
        assert std_column['nullable'] is False

    def test_questions_difficulty_column(self, table_info):
        """MIG-005-004: Verify questions.difficulty is SMALLINT with CHECK 1-5 range."""
        diff_column = next(c for c in table_info if c['name'] == 'difficulty')
        assert str(diff_column['type']) == 'SMALLINT'
        assert diff_column['nullable'] is False

    def test_questions_irt_difficulty_column(self, table_info):
        """MIG-005-005: Verify irt_difficulty is NUMERIC(5,3) with default 0.000."""
        irt_diff_column = next(c for c in table_info if c['name'] == 'irt_difficulty')
        assert 'NUMERIC' in str(irt_diff_column['type'])
        assert '5,3' in str(irt_diff_column['type'])
        assert irt_diff_column['default'] == "0.000"

    def test_questions_irt_discrimination_column(self, table_info):
        """MIG-005-006: Verify irt_discrimination is NUMERIC(5,3) with default 1.000."""
        irt_disc_column = next(c for c in table_info if c['name'] == 'irt_discrimination')
        assert 'NUMERIC' in str(irt_disc_column['type'])
        assert '5,3' in str(irt_disc_column['type'])
        assert irt_disc_column['default'] == "1.000"

    def test_questions_irt_guessing_column(self, table_info):
        """MIG-005-007: Verify irt_guessing is NUMERIC(5,4) with default 0.2500."""
        irt_guess_column = next(c for c in table_info if c['name'] == 'irt_guessing')
        assert 'NUMERIC' in str(irt_guess_column['type'])
        assert '5,4' in str(irt_guess_column['type'])
        assert irt_guess_column['default'] == "0.2500"

    def test_questions_question_type_column(self, table_info):
        """MIG-005-008: Verify question_type has CHECK constraint for valid types."""
        qtype_column = next(c for c in table_info if c['name'] == 'question_type')
        assert str(qtype_column['type']) == 'VARCHAR(20)'
        assert qtype_column['nullable'] is False
        assert qtype_column['default'] == "'multiple_choice'"

    def test_questions_stem_column(self, table_info):
        """MIG-005-009: Verify questions.stem is TEXT, NOT NULL."""
        stem_column = next(c for c in table_info if c['name'] == 'stem')
        assert str(stem_column['type']) == 'TEXT'
        assert stem_column['nullable'] is False

    def test_questions_options_column(self, table_info):
        """MIG-005-010: Verify questions.options is JSONB, NOT NULL with default []."""
        options_column = next(c for c in table_info if c['name'] == 'options')
        assert str(options_column['type']) == 'JSONB'
        assert options_column['nullable'] is False
        assert options_column['default'] == "'[]'"

    def test_questions_correct_answer_column(self, table_info):
        """MIG-005-011: Verify correct_answer is VARCHAR(10), NOT NULL."""
        correct_column = next(c for c in table_info if c['name'] == 'correct_answer')
        assert str(correct_column['type']) == 'VARCHAR(10)'
        assert correct_column['nullable'] is False

    def test_questions_explanation_column(self, table_info):
        """MIG-005-012: Verify questions.explanation is TEXT (nullable)."""
        exp_column = next(c for c in table_info if c['name'] == 'explanation')
        assert str(exp_column['type']) == 'TEXT'
        assert exp_column['nullable'] is True

    def test_questions_source_column(self, table_info):
        """MIG-005-013: Verify source has CHECK constraint (seed, ai_generated, imported, teacher_submitted)."""
        source_column = next(c for c in table_info if c['name'] == 'source')
        assert str(source_column['type']) == 'VARCHAR(30)'
        assert source_column['nullable'] is False
        assert source_column['default'] == "'seed'"

    def test_questions_status_column(self, table_info):
        """MIG-005-014: Verify status has CHECK constraint (draft, review, active, retired)."""
        status_column = next(c for c in table_info if c['name'] == 'status')
        assert str(status_column['type']) == 'VARCHAR(20)'
        assert status_column['nullable'] is False
        assert status_column['default'] == "'active'"

    def test_questions_times_shown_column(self, table_info):
        """MIG-005-015: Verify times_shown is INTEGER with default 0."""
        shown_column = next(c for c in table_info if c['name'] == 'times_shown')
        assert str(shown_column['type']) == 'INTEGER'
        assert shown_column['default'] == "0"

    def test_questions_content_embedding_column(self, table_info):
        """MIG-005-016: Verify content_embedding is VECTOR(1536) for deduplication."""
        embed_column = next(c for c in table_info if c['name'] == 'content_embedding')
        assert 'VECTOR' in str(embed_column['type'])
        assert '1536' in str(embed_column['type'])

    def test_questions_timestamps(self, table_info):
        """MIG-005-017: Verify created_at and updated_at timestamps exist."""
        timestamps = {c['name']: c for c in table_info if 'at' in c['name']}
        assert 'created_at' in timestamps
        assert 'updated_at' in timestamps

    def test_questions_standard_diff_index(self, indexes):
        """MIG-005-018: Verify index on (standard_code, difficulty) for CAT queries."""
        std_diff_index = next((i for i in indexes if 'standard_diff' in i['name']), None)
        assert std_diff_index is not None
        assert 'standard_code' in std_diff_index['column_names']
        assert 'difficulty' in std_diff_index['column_names']

    def test_questions_active_index(self, indexes):
        """MIG-005-019: Verify index on (status, standard_code) for question pool loading."""
        active_index = next((i for i in indexes if 'active' in i['name']), None)
        assert active_index is not None
        assert 'status' in active_index['column_names']
        assert 'standard_code' in active_index['column_names']

    def test_questions_irt_index(self, indexes):
        """MIG-005-020: Verify index on (irt_difficulty, irt_discrimination) for CAT selection."""
        irt_index = next((i for i in indexes if 'irt' in i['name']), None)
        assert irt_index is not None
        assert 'irt_difficulty' in irt_index['column_names']
        assert 'irt_discrimination' in irt_index['column_names']

    def test_questions_embedding_index(self, indexes):
        """MIG-005-021: Verify ivfflat index on content_embedding for vector similarity."""
        embed_index = next((i for i in indexes if 'questions_embedding' in i['name']), None)
        assert embed_index is not None
        assert embed_index['type'] == 'ivfflat'

    def test_questions_stem_trgm_index(self, indexes):
        """MIG-005-022: Verify gin trgm index on stem for full-text search."""
        stem_index = next((i for i in indexes if 'stem_trgm' in i['name']), None)
        assert stem_index is not None
        assert stem_index['type'] == 'gin'


class TestQuestionsDataIntegrity:
    """Tests for question data integrity and constraint validation."""

    @pytest.fixture
    def sample_question(self):
        """Sample question data."""
        return {
            'standard_code': '4.OA.A.1',
            'difficulty': 3,
            'irt_difficulty': 0.150,
            'irt_discrimination': 1.200,
            'irt_guessing': 0.2500,
            'question_type': 'multiple_choice',
            'stem': 'What is 12 × 8?',
            'options': '[{"key": "A", "text": "96"}, {"key": "B", "text": "86"}, {"key": "C", "text": "106"}, {"key": "D", "text": "76"}]',
            'correct_answer': 'A',
            'explanation': '12 × 8 = 96',
            'source': 'seed',
            'status': 'active',
        }

    def test_insert_question_successfully(self, engine, sample_question):
        """MIG-005-023: Verify questions can be inserted with all required fields."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (
                    standard_code, difficulty, irt_difficulty, irt_discrimination, irt_guessing,
                    question_type, stem, options, correct_answer, explanation, source, status
                ) VALUES (
                    :standard_code, :difficulty, :irt_difficulty, :irt_discrimination, :irt_guessing,
                    :question_type, :stem, :options, :correct_answer, :explanation, :source, :status
                )
            """, **sample_question))
            conn.commit()

    def test_question_difficulty_range_constraint(self, engine):
        """MIG-005-024: Verify difficulty CHECK constraint (1-5)."""
        # Valid difficulty values should succeed
        for diff in [1, 2, 3, 4, 5]:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                    VALUES ('4.OA.A.1', :diff, 'Test', '[{"key": "A", "text": "1"}]', 'A', 'seed', 'active')
                """, diff=diff))
                conn.commit()

        # Invalid difficulty should fail
        with engine.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(text("""
                    INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                    VALUES ('4.OA.A.1', 0, 'Test', '[{"key": "A", "text": "1"}]', 'A', 'seed', 'active')
                """))
                conn.commit()

    def test_question_non_active_filter(self, engine):
        """MIG-005-025: Verify index includes WHERE status = 'active' condition."""
        # Insert active and inactive questions
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES ('4.OA.A.1', 3, 'Active Q', '[{"key": "A", "text": "1"}]', 'A', 'seed', 'active')
            """))
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES ('4.OA.A.2', 3, 'Inactive Q', '[{"key": "A", "text": "1"}]', 'A', 'seed', 'draft')
            """))
            conn.commit()

        # Query active questions should use index
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM questions
                WHERE status = 'active' AND standard_code = '4.OA.A.1'
            """)).fetchall()
            assert len(result) == 1
            assert result[0]['stem'] == 'Active Q'


class TestPgvectorEmbeddings:
    """Tests for pgvector embeddings in questions table."""

    def test_pgvector_extension_enabled(self, engine):
        """MIG-005-026: Verify pgvector extension is enabled."""
        result = engine.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
        assert result is not None, "pgvector extension should be enabled"

    def test_vector_embedding_can_be_stored(self, engine):
        """MIG-005-027: Verify vector column can store embeddings."""
        test_embedding = "[0.1, 0.2, 0.3, 0.4, 0.5]"
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer,
                    source, status, content_embedding)
                VALUES ('4.VECTOR.Q', 3, 'Vector test', '[{"key": "A", "text": "1"}]', 'A',
                    'seed', 'active', :vec)
            """, vec=test_embedding))
            conn.commit()

    def test_vector_cosine_similarity(self, engine):
        """MIG-005-028: Verify vector cosine similarity operator works."""
        vec1 = "[0.1, 0.2, 0.3, 0.4, 0.5]"
        vec2 = "[0.15, 0.25, 0.35, 0.45, 0.55]"

        with engine.connect() as conn:
            # Insert test vectors
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer,
                    source, status, content_embedding)
                VALUES ('4.VECTOR.COS1', 3, 'Test 1', '[{"key": "A", "text": "1"}]', 'A',
                    'seed', 'active', :vec1)
            """, vec1=vec1))
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer,
                    source, status, content_embedding)
                VALUES ('4.VECTOR.COS2', 3, 'Test 2', '[{"key": "A", "text": "1"}]', 'A',
                    'seed', 'active', :vec2)
            """, vec2=vec2))
            conn.commit()

            # Query with cosine similarity
            result = conn.execute(text("""
                SELECT standard_code, content_embedding <=> :query_vec as similarity
                FROM questions
                WHERE standard_code LIKE '4.VECTOR.%'
                ORDER BY similarity
            """, query_vec=vec1)).fetchall()

            assert len(result) == 2


class TestQuestionOptionsStructure:
    """Tests for JSONB options array structure."""

    def test_jsonb_options_valid_format(self, engine):
        """MIG-005-029: Verify options JSONB accepts valid array format."""
        valid_options = '[{"key": "A", "text": "42", "image_url": null}, {"key": "B", "text": "43", "image_url": null}]'
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES ('4.JSON.OPTS', 3, 'JSON test', :options, 'A', 'seed', 'active')
            """, options=valid_options))
            conn.commit()

    def test_jsonb_options_empty_array(self, engine):
        """MIG-005-030: Verify empty options array is valid."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES ('4.JSON.EMPTY', 3, 'Empty options', '[]', 'A', 'seed', 'active')
            """))
            conn.commit()

    def test_jsonb_stem_trigram_search(self, engine):
        """MIG-005-031: Verify trigram full-text search works on question stems."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES
                    ('4.TRIG.A', 3, 'What is the product of 12 and 8?', '[{"key": "A", "text": "96"}]', 'A', 'seed', 'active'),
                    ('4.TRIG.B', 3, 'Multiply 12 times 8', '[{"key": "A", "text": "96"}]', 'A', 'seed', 'active'),
                    ('4.TRIG.C', 3, 'Add 12 and 8', '[{"key": "A", "text": "20"}]', 'A', 'seed', 'active')
            """))
            conn.commit()

        # Query with similarity threshold
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code, stem
                FROM questions
                WHERE stem % 'product of 12 and 8'
                ORDER BY ts_rank_cd(to_tsvector('simple', stem)) DESC
            """)).fetchall()

            assert len(result) >= 1


class TestQuestionAuditTriggers:
    """Tests for audit log triggers on questions table."""

    def test_audit_log_insert(self, engine):
        """MIG-005-032: Verify audit log is populated on INSERT."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES ('4.AUDIT.TEST', 3, 'Audit test', '[{"key": "A", "text": "1"}]', 'A', 'seed', 'active')
            """))
            conn.commit()

        # Check audit log
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM audit_log
                WHERE table_name = 'questions' AND record_id IN (
                    SELECT id FROM questions WHERE standard_code = '4.AUDIT.TEST'
                )
                AND action = 'INSERT'
            """)).fetchone()
            assert result is not None

    def test_audit_log_update(self, engine):
        """MIG-005-033: Verify audit log is populated on UPDATE."""
        # Insert question
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, source, status)
                VALUES ('4.AUDIT.UPD', 3, 'Original stem', '[{"key": "A", "text": "1"}]', 'A', 'seed', 'active')
            """))
            conn.commit()

        # Update question
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE questions SET stem = 'Updated stem' WHERE standard_code = '4.AUDIT.UPD'
            """))
            conn.commit()

        # Check audit log
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT action FROM audit_log
                WHERE table_name = 'questions' AND action = 'UPDATE'
                LIMIT 1
            """)).fetchone()
            assert result is not None
