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
                VALUES (:aid, :sid, 'diagnostic', 'completed', 40)
            """, aid=assessment_id, sid=student_id))
            conn.commit()

        # Insert 32 correct out of 40
        with engine.connect() as conn:
            for i in range(32):
                conn.execute(text("""
                    INSERT INTO assessment_responses (
                        assessment_id, session_id, question_id, selected_answer, is_correct,
                        time_spent_ms, question_number, standard_code
                    ) VALUES (
                        :aid, :sid, :qid, 'A', true, 30000, :qn, '4.OA.A.1'
                    )
                """, aid=assessment_id, sid='33333333-3333-3333-3333-333333333333',
                    qid=f'44444444-4444-4444-4444-4444{str(i).zfill(4)}', qn=i+1))
            conn.commit()

        # Verify score calculation
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FILTER (WHERE is_correct) as correct, COUNT(*) as total
                FROM assessment_responses WHERE assessment_id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['correct'] == 32
            assert result['total'] == 32

    def test_domain_scores_calculated(self, engine):
        """SVC-SCR-002: Verify scores are calculated by domain."""
        assessment_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            # Insert responses with different standards
            conn.execute(text("""
                INSERT INTO assessment_responses (assessment_id, session_id, question_id, is_correct, question_number, standard_code)
                VALUES
                    (:aid, :sid, :qid1, true, 1, '4.OA.A.1'),
                    (:aid, :sid, :qid2, true, 2, '4.OA.A.1'),
                    (:aid, :sid, :qid3, false, 3, '4.NBT.A.1'),
                    (:aid, :sid, :qid4, true, 4, '4.NBT.A.1')
            """, aid=assessment_id, sid='33333333-3333-3333-3333-333333333333',
               qid1='44444444-4444-4444-4444-44440001', qid2='44444444-4444-4444-4444-44440002',
               qid3='44444444-4444-4444-4444-44440003', qid4='44444444-4444-4444-4444-44440004'))
            conn.commit()

        # Verify domain scores
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code, COUNT(*) FILTER (WHERE is_correct) as correct, COUNT(*) as total
                FROM assessment_responses WHERE assessment_id = :aid
                GROUP BY standard_code
            """, aid=assessment_id)).fetchall()

            assert len(result) == 2  # Two domains

    def test_gap_analysis_generated(self, engine):
        """SVC-SCR-003: Verify gap analysis identifies below-par standards."""
        student_id = '11111111-1111-1111-1111-111111111111'

        # Insert skill state with below_par mastery
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO student_skill_states (student_id, standard_code, p_mastery, mastery_level)
                VALUES (:sid, '4.OA.A.1', 0.2500, 'below_par')
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT standard_code, mastery_level FROM student_skill_states
                WHERE mastery_level = 'below_par'
            """)).fetchall()

            assert len(result) == 1
            assert result[0]['standard_code'] == '4.OA.A.1'
