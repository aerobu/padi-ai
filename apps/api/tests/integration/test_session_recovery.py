"""
Test Suite: Integration - Session Recovery Flow

Purpose: Validate assessment session recovery for browser close/reopen scenarios.

COPPA Relevance: Ensures student assessment progress is preserved.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timezone


class TestAssessmentSessionRecovery:
    """Tests for assessment session recovery."""

    def test_assessment_session_created(self, engine):
        """INT-SES-001: Verify assessment session can be created."""
        student_id = '11111111-1111-1111-1111-111111111111'
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status)
                VALUES (:aid, :sid, 'diagnostic', 'in_progress')
            """, aid=assessment_id, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['status'] == 'in_progress'

    def test_assessment_session_with_session_number(self, engine):
        """INT-SES-002: Verify assessment session tracks session number."""
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessment_sessions (assessment_id, session_number, status)
                VALUES (:aid, 1, 'active')
            """, aid=assessment_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT session_number FROM assessment_sessions WHERE assessment_id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['session_number'] == 1

    def test_assessment_session_duration_tracked(self, engine):
        """INT-SES-003: Verify assessment session tracks duration."""
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessment_sessions (assessment_id, session_number, status, duration_ms)
                VALUES (:aid, 1, 'completed', 120000)
            """, aid=assessment_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT duration_ms FROM assessment_sessions WHERE assessment_id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['duration_ms'] == 120000

    def test_assessment_response_persisted(self, engine):
        """INT-SES-004: Verify assessment responses are persisted."""
        assessment_id = '22222222-2222-2222-2222-222222222222'
        session_id = '33333333-3333-3333-3333-333333333333'
        question_id = '44444444-4444-4444-4444-444444444444'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessment_responses (
                    assessment_id, session_id, question_id, selected_answer, is_correct,
                    time_spent_ms, question_number, standard_code
                ) VALUES (
                    :aid, :sid, :qid, 'A', true, 30000, 1, '4.OA.A.1'
                )
            """, aid=assessment_id, sid=session_id, qid=question_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT is_correct FROM assessment_responses WHERE assessment_id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['is_correct'] is True

    def test_assessment_completion_recorded(self, engine):
        """INT-SES-005: Verify assessment completion is recorded."""
        student_id = '11111111-1111-1111-1111-111111111111'
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status, total_questions, total_correct, completed_at)
                VALUES (:aid, :sid, 'diagnostic', 'completed', 40, 32, :completed_at)
            """, aid=assessment_id, sid=student_id, completed_at=datetime.now(timezone.utc)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status, total_correct FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['status'] == 'completed'
            assert result['total_correct'] == 32
