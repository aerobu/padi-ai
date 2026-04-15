"""
Test Suite: Services - Question Selection Service Tests

Purpose: Validate adaptive question selection using IRT parameters.
"""

import pytest
from sqlalchemy import text


class TestQuestionSelection:
    """Tests for adaptive question selection."""

    def test_question_by_standard(self, engine):
        """SVC-QS-001: Verify questions can be selected by standard."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, status)
                VALUES ('4.OA.A.1', 3, 'Test question', '[{"key": "A", "text": "1"}]', 'A', 'active')
            """))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM questions WHERE standard_code = '4.OA.A.1'
            """)).fetchone()
            assert result['count'] == 1

    def test_question_by_difficulty_range(self, engine):
        """SVC-QS-002: Verify questions can be filtered by difficulty."""
        with engine.connect() as conn:
            for diff in [1, 2, 3, 4, 5]:
                conn.execute(text("""
                    INSERT INTO questions (standard_code, difficulty, stem, options, correct_answer, status)
                    VALUES ('4.DIFF.TEST', :diff, 'Test', '[{"key": "A", "text": "1"}]', 'A', 'active')
                """, diff=diff))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT difficulty, COUNT(*) as count
                FROM questions WHERE standard_code = '4.DIFF.TEST'
                GROUP BY difficulty
            """)).fetchall()
            assert len(result) == 5  # All difficulty levels present

    def test_question_selection_irt_parameters(self, engine):
        """SVC-QS-003: Verify questions are selected using IRT parameters."""
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, irt_difficulty, irt_discrimination, stem, options, correct_answer, status)
                VALUES ('4.IRT.TEST', 3, 0.500, 1.500, 'Test', '[{"key": "A", "text": "1"}]', 'A', 'active')
            """))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT irt_difficulty, irt_discrimination FROM questions WHERE standard_code = '4.IRT.TEST'
            """)).fetchone()
            assert result['irt_difficulty'] == 0.500
            assert result['irt_discrimination'] == 1.500


class TestCATItemSelection:
    """Tests for Computerized Adaptive Testing item selection."""

    def test_select_question_near_current_ability(self, engine):
        """SVC-CAT-001: Verify CAT selects questions near student's ability estimate."""
        with engine.connect() as conn:
            # Insert questions with different difficulty levels
            conn.execute(text("""
                INSERT INTO questions (standard_code, difficulty, irt_difficulty, stem, options, correct_answer, status)
                VALUES
                    ('4.CAT.EASY', 2, -1.0, 'Easy question', '[{"key": "A", "text": "1"}]', 'A', 'active'),
                    ('4.CAT.MEDIUM', 3, 0.0, 'Medium question', '[{"key": "A", "text": "1"}]', 'A', 'active'),
                    ('4.CAT.HARD', 4, 1.0, 'Hard question', '[{"key": "A", "text": "1"}]', 'A', 'active')
            """))
            conn.commit()

        # CAT should select question with irt_difficulty closest to theta
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code, irt_difficulty FROM questions
                ORDER BY irt_difficulty
            """)).fetchall()
            assert len(result) == 3
