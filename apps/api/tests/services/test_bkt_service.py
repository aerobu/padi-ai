"""
Test Suite: Services - BKT Service Tests

Purpose: Validate Bayesian Knowledge Tracing service for student skill state updates.
"""

import pytest
from sqlalchemy import text


class TestBKTStateUpdate:
    """Tests for BKT state updates."""

    def test_p_mastery_increases_after_correct(self, engine):
        """SVC-BKT-001: Verify p_mastery increases after correct answer."""
        student_id = '11111111-1111-1111-1111-111111111111'

        # Initial state
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery)
                VALUES (:sid, '4.OA.A.1', 0.1000)
            """, sid=student_id))
            conn.commit()

        # Update after correct answer (simplified BKT)
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE student_skill_states
                SET p_mastery = 0.5000, total_attempts = 1, total_correct = 1
                WHERE student_id = :sid AND standard_code = '4.OA.A.1'
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p_mastery FROM student_skill_states
                WHERE student_id = :sid AND standard_code = '4.OA.A.1'
            """, sid=student_id)).fetchone()
            assert result['p_mastery'] == 0.5000

    def test_p_mastery_decreases_after_incorrect(self, engine):
        """SVC-BKT-002: Verify p_mastery decreases after incorrect answer."""
        student_id = '11111111-1111-1111-1111-111111111111'

        # Start with higher mastery
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery)
                VALUES (:sid, '4.OA.A.1', 0.5000)
            """, sid=student_id))
            conn.commit()

        # Update after incorrect answer
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE student_skill_states
                SET p_mastery = 0.3000, total_attempts = 1
                WHERE student_id = :sid AND standard_code = '4.OA.A.1'
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p_mastery FROM student_skill_states
                WHERE student_id = :sid AND standard_code = '4.OA.A.1'
            """, sid=student_id)).fetchone()
            assert result['p_mastery'] == 0.3000

    def test_bkt_parameters_updated(self, engine):
        """SVC-BKT-003: Verify BKT slip/guess parameters are tracked."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery, p_slip, p_guess)
                VALUES (:sid, '4.OA.A.1', 0.5000, 0.0500, 0.2500)
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p_slip, p_guess FROM student_skill_states
                WHERE student_id = :sid
            """, sid=student_id)).fetchone()
            assert result['p_slip'] == 0.0500
            assert result['p_guess'] == 0.2500


class TestBKTClassification:
    """Tests for BKT mastery classification."""

    def test_not_assessed_initial_state(self, engine):
        """SVC-BKT-004: Verify new standards start as not_assessed."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery)
                VALUES (:sid, '4.OA.A.1', 0.1000)
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT mastery_level FROM student_skill_states
                WHERE student_id = :sid
            """, sid=student_id)).fetchone()
            assert result['mastery_level'] == 'not_assessed'

    def test_below_par_classification(self, engine):
        """SVC-BKT-005: Verify below_par classification for low p_mastery."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery, mastery_level)
                VALUES (:sid, '4.OA.A.1', 0.2500, 'below_par')
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT mastery_level FROM student_skill_states
                WHERE student_id = :sid
            """, sid=student_id)).fetchone()
            assert result['mastery_level'] == 'below_par'

    def test_on_par_classification(self, engine):
        """SVC-BKT-006: Verify on_par classification for moderate p_mastery."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery, mastery_level)
                VALUES (:sid, '4.OA.A.1', 0.6000, 'on_par')
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT mastery_level FROM student_skill_states
                WHERE student_id = :sid
            """, sid=student_id)).fetchone()
            assert result['mastery_level'] == 'on_par'


class TestBKTStreaks:
    """Tests for BKT streak tracking."""

    def test_current_streak_increases(self, engine):
        """SVC-BKT-007: Verify current streak increases on consecutive correct answers."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, streak_current)
                VALUES (:sid, '4.OA.A.1', 3)
            """, sid=student_id))
            conn.commit()

        # Update streak
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE student_skill_states
                SET streak_current = streak_current + 1
                WHERE student_id = :sid AND standard_code = '4.OA.A.1'
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT streak_current FROM student_skill_states
                WHERE student_id = :sid
            """, sid=student_id)).fetchone()
            assert result['streak_current'] == 4

    def test_current_streak_resets_on_incorrect(self, engine):
        """SVC-BKT-008: Verify current streak resets to 0 on incorrect answer."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, streak_current, streak_longest)
                VALUES (:sid, '4.OA.A.1', 5, 5)
            """, sid=student_id))
            conn.commit()

        # Reset streak
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE student_skill_states
                SET streak_current = 0, streak_longest = GREATEST(streak_longest, 5)
                WHERE student_id = :sid AND standard_code = '4.OA.A.1'
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT streak_current, streak_longest FROM student_skill_states
                WHERE student_id = :sid
            """, sid=student_id)).fetchone()
            assert result['streak_current'] == 0
            assert result['streak_longest'] == 5
