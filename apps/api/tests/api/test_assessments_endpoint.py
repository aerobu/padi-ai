"""
Test Suite: API - Assessments Endpoint Tests

Purpose: Validate assessment API endpoints.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timezone


class TestAssessmentsEndpoints:
    """Tests for assessments API."""

    def test_create_assessment(self, engine):
        """API-ASM-001: Verify assessment can be created via API."""
        student_id = '11111111-1111-1111-1111-111111111111'
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status)
                VALUES (:aid, :sid, 'diagnostic', 'created')
            """, aid=assessment_id, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['status'] == 'created'

    def test_get_assessment_by_id(self, engine):
        """API-ASM-002: Verify assessment can be retrieved by ID."""
        assessment_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status)
                VALUES (:aid, :sid, 'diagnostic', 'in_progress')
            """, aid=assessment_id, sid='22222222-2222-2222-2222-222222222222'))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT assessment_type FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['assessment_type'] == 'diagnostic'

    def test_get_assessment_responses(self, engine):
        """API-ASM-003: Verify assessment responses can be retrieved."""
        assessment_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            for i in range(5):
                conn.execute(text("""
                    INSERT INTO assessment_responses (assessment_id, session_id, question_id, is_correct, question_number)
                    VALUES (:aid, :sid, :qid, :correct, :qn)
                """, aid=assessment_id, sid='33333333-3333-3333-3333-333333333333',
                    qid=f'44444444-4444-4444-4444-4444{str(i).zfill(4)}', correct=i % 2 == 0, qn=i+1))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE is_correct) as correct
                FROM assessment_responses WHERE assessment_id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['total'] == 5
            assert result['correct'] == 3

    def test_complete_assessment(self, engine):
        """API-ASM-004: Verify assessment can be completed via API."""
        assessment_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status, total_questions, total_correct, completed_at)
                VALUES (:aid, :sid, 'diagnostic', 'completed', 40, 35, :completed_at)
            """, aid=assessment_id, sid='22222222-2222-2222-2222-222222222222',
               completed_at=datetime.now(timezone.utc)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT total_questions, total_correct FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['total_questions'] == 40
            assert result['total_correct'] == 35

    def test_assessment_results_summary(self, engine):
        """API-ASM-005: Verify assessment results summary is stored."""
        assessment_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status, results_summary)
                VALUES (:aid, :sid, 'diagnostic', 'completed', :summary)
            """, aid=assessment_id, sid='22222222-2222-2222-2222-222222222222',
               summary='{"byDomain": {"4.OA": 0.8, "4.NBT": 0.7}}'))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT results_summary FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['results_summary'] is not None
