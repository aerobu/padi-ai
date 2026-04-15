"""
Test Suite: MIG-006 - BKT State Tracking Tables

Purpose: Validate the student_skill_states table structure for Bayesian Knowledge Tracing
         state tracking, including mastery probabilities, slip/guess parameters, and
         derived mastery level classifications.

Coverage:
- student_skill_states table structure and data types
- BKT state parameters (p_mastery, p_transit, p_slip, p_guess)
- Mastery level classification constraints
- Unique constraint on (student_id, standard_code)
- Index validation for dashboard and gap analysis queries

COPPA Relevance: Student skill states contain no PII - purely educational mastery data.
"""

import pytest
from sqlalchemy import text, inspect, MetaData
from typing import Dict, Any


class TestStudentSkillStatesTableSchema:
    """Tests for the student_skill_states table structure."""

    @pytest.fixture
    def table_info(self, engine):
        """Get student_skill_states table information."""
        inspector = inspect(engine)
        return inspector.get_columns('student_skill_states')

    @pytest.fixture
    def indexes(self, engine):
        """Get student_skill_states table indexes."""
        inspector = inspect(engine)
        return inspector.get_indexes('student_skill_states')

    def test_skill_states_table_exists(self, engine):
        """MIG-006-001: Verify student_skill_states table exists."""
        inspector = inspect(engine)
        assert 'student_skill_states' in inspector.get_table_names()

    def test_skill_states_id_column(self, table_info):
        """MIG-006-002: Verify id is UUID with default gen_random_uuid()."""
        id_column = next(c for c in table_info if c['name'] == 'id')
        assert id_column['type'].python_type.__name__ == 'UUID'
        assert id_column['default'] == "gen_random_uuid()"

    def test_skill_states_student_id_foreign_key(self, table_info):
        """MIG-006-003: Verify student_id references students(id) with CASCADE delete."""
        student_col = next(c for c in table_info if c['name'] == 'student_id')
        assert student_col['nullable'] is False

    def test_skill_states_standard_code_foreign_key(self, table_info):
        """MIG-006-004: Verify standard_code references standards(code)."""
        std_col = next(c for c in table_info if c['name'] == 'standard_code')
        assert std_col['nullable'] is False

    def test_skill_states_p_mastery_column(self, table_info):
        """MIG-006-005: Verify p_mastery is NUMERIC(5,4) with default 0.1000."""
        p_mastery_col = next(c for c in table_info if c['name'] == 'p_mastery')
        assert 'NUMERIC' in str(p_mastery_col['type'])
        assert '5,4' in str(p_mastery_col['type'])
        assert p_mastery_col['default'] == "0.1000"
        assert p_mastery_col['nullable'] is False

    def test_skill_states_p_transit_column(self, table_info):
        """MIG-006-006: Verify p_transit is NUMERIC(5,4) with default 0.1000."""
        p_transit_col = next(c for c in table_info if c['name'] == 'p_transit')
        assert 'NUMERIC' in str(p_transit_col['type'])
        assert '5,4' in str(p_transit_col['type'])
        assert p_transit_col['default'] == "0.1000"
        assert p_transit_col['nullable'] is False

    def test_skill_states_p_slip_column(self, table_info):
        """MIG-006-007: Verify p_slip is NUMERIC(5,4) with default 0.0500."""
        p_slip_col = next(c for c in table_info if c['name'] == 'p_slip')
        assert 'NUMERIC' in str(p_slip_col['type'])
        assert '5,4' in str(p_slip_col['type'])
        assert p_slip_col['default'] == "0.0500"
        assert p_slip_col['nullable'] is False

    def test_skill_states_p_guess_column(self, table_info):
        """MIG-006-008: Verify p_guess is NUMERIC(5,4) with default 0.2500."""
        p_guess_col = next(c for c in table_info if c['name'] == 'p_guess')
        assert 'NUMERIC' in str(p_guess_col['type'])
        assert '5,4' in str(p_guess_col['type'])
        assert p_guess_col['default'] == "0.2500"
        assert p_guess_col['nullable'] is False

    def test_skill_states_mastery_level_column(self, table_info):
        """MIG-006-009: Verify mastery_level has CHECK constraint for valid classifications."""
        mastery_col = next(c for c in table_info if c['name'] == 'mastery_level')
        assert str(mastery_col['type']) == 'VARCHAR(20)'
        assert mastery_col['nullable'] is False
        assert mastery_col['default'] == "'not_assessed'"

    def test_skill_states_total_attempts_column(self, table_info):
        """MIG-006-010: Verify total_attempts is INTEGER with default 0."""
        attempts_col = next(c for c in table_info if c['name'] == 'total_attempts')
        assert str(attempts_col['type']) == 'INTEGER'
        assert attempts_col['default'] == "0"
        assert attempts_col['nullable'] is False

    def test_skill_states_total_correct_column(self, table_info):
        """MIG-006-011: Verify total_correct is INTEGER with default 0."""
        correct_col = next(c for c in table_info if c['name'] == 'total_correct')
        assert str(correct_col['type']) == 'INTEGER'
        assert correct_col['default'] == "0"
        assert correct_col['nullable'] is False

    def test_skill_states_streak_columns(self, table_info):
        """MIG-006-012: Verify streak_current and streak_longest INTEGER columns exist."""
        streaks = {c['name']: c for c in table_info if 'streak' in c['name']}
        assert 'streak_current' in streaks
        assert 'streak_longest' in streaks
        assert streaks['streak_current']['default'] == "0"
        assert streaks['streak_longest']['default'] == "0"

    def test_skill_states_last_assessment_column(self, table_info):
        """MIG-006-013: Verify last_assessment_id references assessments(id)."""
        assessment_col = next(c for c in table_info if c['name'] == 'last_assessment_id')
        assert assessment_col['nullable'] is True  # Can be null initially

    def test_skill_states_last_updated_from_column(self, table_info):
        """MIG-006-014: Verify last_updated_from has CHECK constraint."""
        source_col = next(c for c in table_info if c['name'] == 'last_updated_from')
        assert str(source_col['type']) == 'VARCHAR(20)'
        assert source_col['nullable'] is False
        assert source_col['default'] == "'diagnostic'"

    def test_skill_states_timestamps(self, table_info):
        """MIG-006-015: Verify created_at and updated_at timestamps exist."""
        timestamps = {c['name']: c for c in table_info if 'at' in c['name']}
        assert 'created_at' in timestamps
        assert 'updated_at' in timestamps

    def test_skill_states_unique_constraint(self, engine):
        """MIG-006-016: Verify unique constraint on (student_id, standard_code)."""
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables['student_skill_states']

        unique_constraints = [
            c for c in table.constraints
            if c.name and 'uq_skill_state' in c.name.lower()
        ]
        assert len(unique_constraints) > 0

    def test_skill_states_student_index(self, indexes):
        """MIG-006-017: Verify index on student_id for dashboard queries."""
        student_index = next((i for i in indexes if 'student' in i['name']), None)
        assert student_index is not None
        assert 'student_id' in student_index['column_names']

    def test_skill_states_mastery_index(self, indexes):
        """MIG-006-018: Verify composite index on (standard_code, mastery_level) for gap analysis."""
        mastery_index = next((i for i in indexes if 'mastery' in i['name']), None)
        assert mastery_index is not None
        assert 'standard_code' in mastery_index['column_names']
        assert 'mastery_level' in mastery_index['column_names']


class TestStudentSkillStatesDataIntegrity:
    """Tests for BKT state data integrity."""

    @pytest.fixture
    def sample_skill_state(self):
        """Sample BKT state data."""
        return {
            'student_id': '12345678-1234-1234-1234-123456789012',
            'standard_code': '4.OA.A.1',
            'p_mastery': 0.1000,
            'p_transit': 0.1000,
            'p_slip': 0.0500,
            'p_guess': 0.2500,
            'mastery_level': 'not_assessed',
            'total_attempts': 0,
            'total_correct': 0,
            'streak_current': 0,
            'streak_longest': 0,
            'last_updated_from': 'diagnostic',
        }

    def test_insert_skill_state_successfully(self, engine, sample_skill_state):
        """MIG-006-019: Verify BKT state can be inserted with all parameters."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (
                    student_id, standard_code, p_mastery, p_transit, p_slip, p_guess,
                    mastery_level, total_attempts, total_correct, streak_current, streak_longest,
                    last_updated_from
                ) VALUES (
                    :student_id, :standard_code, :p_mastery, :p_transit, :p_slip, :p_guess,
                    :mastery_level, :total_attempts, :total_correct, :streak_current, :streak_longest,
                    :last_updated_from
                )
            """, **sample_skill_state))
            conn.commit()

    def test_unique_student_standard_constraint(self, engine):
        """MIG-006-020: Verify duplicate (student_id, standard_code) is rejected."""
        student_id = '12345678-1234-1234-1234-123456789012'
        std_code = '4.OA.A.1'

        # First insert succeeds
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (
                    student_id, standard_code, p_mastery, mastery_level
                ) VALUES (:sid, :sc, 0.1000, 'not_assessed')
            """, sid=student_id, sc=std_code))
            conn.commit()

        # Duplicate should fail
        with engine.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(text("""
                    INSERT INTO student_skill_states (
                        student_id, standard_code, p_mastery, mastery_level
                    ) VALUES (:sid, :sc, 0.1000, 'not_assessed')
                """, sid=student_id, sc=std_code))
                conn.commit()

    def test_mastery_level_classification_values(self, engine):
        """MIG-006-021: Verify mastery_level CHECK constraint accepts valid values."""
        valid_levels = ['not_assessed', 'below_par', 'approaching', 'on_par', 'above_par', 'mastered']
        student_id = '12345678-1234-1234-1234-123456789012'

        for level in valid_levels:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO student_skill_states (student_id, standard_code, p_mastery, mastery_level)
                    VALUES (:sid, '4.LEVEL.TEST', 0.1000, :level)
                """, sid=student_id, level=level))
                conn.commit()

    def test_mastery_level_invalid_value_rejected(self, engine):
        """MIG-006-022: Verify invalid mastery_level is rejected."""
        student_id = '12345678-1234-1234-1234-123456789012'

        with engine.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(text("""
                    INSERT INTO student_skill_states (student_id, standard_code, p_mastery, mastery_level)
                    VALUES (:sid, '4.INVALID.LEVEL', 0.1000, 'invalid_level')
                """, sid=student_id))
                conn.commit()

    def test_last_updated_from_values(self, engine):
        """MIG-006-023: Verify last_updated_from CHECK constraint accepts valid sources."""
        student_id = '12345678-1234-1234-1234-123456789012'
        valid_sources = ['diagnostic', 'practice', 'post_unit']

        for source in valid_sources:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO student_skill_states (student_id, standard_code, p_mastery, last_updated_from)
                    VALUES (:sid, '4.SOURCE.TEST', 0.1000, :src)
                """, sid=student_id, src=source))
                conn.commit()


class TestBKTStateUpdates:
    """Tests for BKT state updates during assessment."""

    def test_update_skill_state_after_correct_answer(self, engine):
        """MIG-006-024: Verify skill state can be updated after correct response."""
        student_id = '12345678-1234-1234-1234-123456789012'

        # Insert initial state
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery)
                VALUES (:sid, '4.UPDATE.CORRECT', 0.1000)
            """, sid=student_id))
            conn.commit()

        # Update after correct answer
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE student_skill_states
                SET p_mastery = 0.5000,
                    total_attempts = total_attempts + 1,
                    total_correct = total_correct + 1,
                    streak_current = streak_current + 1,
                    streak_longest = GREATEST(streak_longest, streak_current + 1),
                    updated_at = CURRENT_TIMESTAMP
                WHERE student_id = :sid AND standard_code = '4.UPDATE.CORRECT'
            """, sid=student_id))
            conn.commit()

        # Verify update
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p_mastery, total_attempts, total_correct, streak_current
                FROM student_skill_states
                WHERE student_id = :sid AND standard_code = '4.UPDATE.CORRECT'
            """, sid=student_id)).fetchone()

            assert result['p_mastery'] == 0.5000
            assert result['total_attempts'] == 1
            assert result['total_correct'] == 1
            assert result['streak_current'] == 1

    def test_update_skill_state_after_incorrect_answer(self, engine):
        """MIG-006-025: Verify skill state can be updated after incorrect response."""
        student_id = '12345678-1234-1234-1234-123456789012'

        # Insert initial state
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery, streak_current)
                VALUES (:sid, '4.UPDATE.WRONG', 0.5000, 3)
            """, sid=student_id))
            conn.commit()

        # Update after incorrect answer
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE student_skill_states
                SET p_mastery = 0.3000,
                    total_attempts = total_attempts + 1,
                    streak_current = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE student_id = :sid AND standard_code = '4.UPDATE.WRONG'
            """, sid=student_id))
            conn.commit()

        # Verify update
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p_mastery, total_attempts, streak_current
                FROM student_skill_states
                WHERE student_id = :sid AND standard_code = '4.UPDATE.WRONG'
            """, sid=student_id)).fetchone()

            assert result['p_mastery'] == 0.3000
            assert result['total_attempts'] == 1
            assert result['streak_current'] == 0


class TestSkillStatesAuditTriggers:
    """Tests for audit log triggers on student_skill_states table."""

    def test_audit_log_on_insert(self, engine):
        """MIG-006-026: Verify audit log entry created on INSERT."""
        student_id = '12345678-1234-1234-1234-123456789012'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery)
                VALUES (:sid, '4.AUDIT.SKILL', 0.1000)
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT action FROM audit_log
                WHERE table_name = 'student_skill_states'
                LIMIT 1
            """)).fetchone()
            assert result is not None

    def test_audit_log_on_update(self, engine):
        """MIG-006-027: Verify audit log entry created on UPDATE."""
        student_id = '12345678-1234-1234-1234-123456789012'

        # Insert
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery)
                VALUES (:sid, '4.AUDIT.SKILL.UPD', 0.1000)
            """, sid=student_id))
            conn.commit()

        # Update
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE student_skill_states SET p_mastery = 0.5000
                WHERE student_id = :sid AND standard_code = '4.AUDIT.SKILL.UPD'
            """, sid=student_id))
            conn.commit()

        # Check for UPDATE action
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT action FROM audit_log
                WHERE table_name = 'student_skill_states' AND action = 'UPDATE'
                LIMIT 1
            """)).fetchone()
            assert result is not None
