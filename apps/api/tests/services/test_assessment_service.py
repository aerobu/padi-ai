"""
Test Suite: Services - Assessment Service Tests

Purpose: Validate assessment lifecycle management.
"""

import pytest
from sqlalchemy import text
from datetime import datetime, timezone


class TestAssessmentLifecycle:
    """Tests for assessment lifecycle."""

    def test_assessment_created(self, engine):
        """SVC-ASM-001: Verify assessment can be created."""
        student_id = '11111111-1111-1111-1111-111111111111'
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status, target_question_count)
                VALUES (:aid, :sid, 'diagnostic', 'created', 40)
            """, aid=assessment_id, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['status'] == 'created'

    def test_assessment_started(self, engine):
        """SVC-ASM-002: Verify assessment can be started."""
        student_id = '11111111-1111-1111-1111-111111111111'
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status, started_at)
                VALUES (:aid, :sid, 'diagnostic', 'in_progress', :started_at)
            """, aid=assessment_id, sid=student_id, started_at=datetime.now(timezone.utc)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['status'] == 'in_progress'

    def test_assessment_completed(self, engine):
        """SVC-ASM-003: Verify assessment can be completed."""
        student_id = '11111111-1111-1111-1111-111111111111'
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status, total_questions, total_correct, completed_at)
                VALUES (:aid, :sid, 'diagnostic', 'completed', 40, 35, :completed_at)
            """, aid=assessment_id, sid=student_id, completed_at=datetime.now(timezone.utc)))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT total_questions, total_correct FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['total_questions'] == 40
            assert result['total_correct'] == 35

    def test_assessment_paused(self, engine):
        """SVC-ASM-004: Verify assessment can be paused."""
        student_id = '11111111-1111-1111-1111-111111111111'
        assessment_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO assessments (id, student_id, assessment_type, status)
                VALUES (:aid, :sid, 'diagnostic', 'in_progress')
            """, aid=assessment_id, sid=student_id))
            conn.commit()

        # Pause assessment
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE assessments SET status = 'paused' WHERE id = :aid
            """, aid=assessment_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT status FROM assessments WHERE id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['status'] == 'paused'


class TestAssessmentProgress:
    """Tests for assessment progress tracking."""

    def test_questions_answered_counted(self, engine):
        """SVC-ASM-005: Verify question count is tracked."""
        assessment_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            for i in range(10):
                conn.execute(text("""
                    INSERT INTO assessment_responses (assessment_id, session_id, question_id, is_correct, question_number)
                    VALUES (:aid, :sid, :qid, true, :qn)
                """, aid=assessment_id, sid='33333333-3333-3333-3333-333333333333',
                    qid=f'44444444-4444-4444-4444-4444{str(i).zfill(4)}', qn=i+1))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as answered FROM assessment_responses WHERE assessment_id = :aid
            """, aid=assessment_id)).fetchone()
            assert result['answered'] == 10
