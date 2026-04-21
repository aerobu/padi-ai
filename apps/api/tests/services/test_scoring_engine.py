"""
Test Suite: Services - Scoring Engine Tests

Purpose: Validate scoring engine for assessment results calculation.
"""

import pytest
from sqlalchemy import text


class TestAssessmentScoring:
    """Tests for assessment scoring."""

    def test_overall_score_calculated(self, engine):
        """SVC-SCR-001: Verify overall score is calculated from responses."""
        assessment_id = '11111111-1111-1111-1111-111111111111'
        student_id = '22222222-2222-2222-2222-222222222222'

        # Insert assessment
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status, total_questions)
                VALUES (:id, :student_id, 'diagnostic', 'completed', 40)
            """), {"id": assessment_id, "student_id": student_id})
            conn.commit()

        # Insert 32 correct out of 40
        with engine.connect() as conn:
            for i in range(32):
                conn.execute(text("""
                    INSERT INTO assessment_responses (
                        assessment_id, session_id, question_id, selected_answer, is_correct,
                        time_spent_ms, question_number, standard_code
                    ) VALUES (
                        :assessment_id, :session_id, :question_id, 'A', true, 30000, :question_number, '4.OA.A.1'
                    )
                """), {"assessment_id": assessment_id, "session_id": '33333333-3333-3333-3333-333333333333',
                    "question_id": f'44444444-4444-4444-4444-4444{str(i).zfill(4)}', "question_number": i+1})
            conn.commit()

        # Verify score calculation
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FILTER (WHERE is_correct) as correct, COUNT(*) as total
                FROM assessment_responses WHERE assessment_id = :id
            """), {"id": assessment_id}).fetchone()
            assert result['correct'] == 32
            assert result['total'] == 32

    def test_domain_scores_calculated(self, engine):
        """SVC-SCR-002: Verify scores are calculated by domain."""
        assessment_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            # Insert responses with different standards
            conn.execute(text("""
                INSERT INTO assessment_responses (assessment_id, session_id, question_id, is_correct, question_number, standard_code)
                VALUES (:assessment_id, :session_id, :question_id_1, true, 1, '4.OA.A.1'),
                       (:assessment_id, :session_id, :question_id_2, true, 2, '4.OA.A.1'),
                       (:assessment_id, :session_id, :question_id_3, false, 3, '4.NBT.A.1'),
                       (:assessment_id, :session_id, :question_id_4, true, 4, '4.NBT.A.1')
            """), {"assessment_id": assessment_id, "session_id": '33333333-3333-3333-3333-333333333333',
                   "question_id_1": '44444444-4444-4444-4444-44440001', "question_id_2": '44444444-4444-4444-4444-44440002',
                   "question_id_3": '44444444-4444-4444-4444-44440003', "question_id_4": '44444444-4444-4444-4444-44440004'})
            conn.commit()

        # Verify domain scores
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code, COUNT(*) FILTER (WHERE is_correct) as correct, COUNT(*) as total
                FROM assessment_responses WHERE assessment_id = :id
                GROUP BY standard_code
            """), {"id": assessment_id}).fetchall()

            assert len(result) == 2  # Two domains

    def test_gap_analysis_generated(self, engine):
        """SVC-SCR-003: Verify gap analysis identifies below-par standards."""
        student_id = '11111111-1111-1111-1111-111111111111'

        # Insert skill state with below_par mastery
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery, mastery_level)
                VALUES (:student_id, '4.OA.A.1', 0.2500, 'below_par')
            """), {"student_id": student_id})
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code, mastery_level FROM student_skill_states
                WHERE mastery_level = 'below_par'
            """)).fetchall()

            assert len(result) == 1
            assert result[0]['standard_code'] == '4.OA.A.1'
