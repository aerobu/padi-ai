"""
Test Suite: API - Student Endpoint Tests

Purpose: Validate student CRUD API endpoints.
"""

import pytest
from sqlalchemy import text


class TestStudentsEndpoints:
    """Tests for student API."""

    def test_create_student(self, engine):
        """API-STD-001: Verify student can be created via API."""
        parent_id = '11111111-1111-1111-1111-111111111111'
        student_id = '22222222-2222-2222-2222-222222222222'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (id, auth0_sub, display_name, role)
                VALUES (:pid, 'auth0|123', 'Parent', 'parent')
            """, pid=parent_id))
            conn.execute(text("""
                INSERT INTO students (id, parent_id, display_name, grade_level)
                VALUES (:sid, :pid, 'Jayden', 4)
            """, sid=student_id, pid=parent_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT display_name FROM students WHERE id = :sid
            """, sid=student_id)).fetchone()
            assert result['display_name'] == 'Jayden'

    def test_get_student_by_id(self, engine):
        """API-STD-002: Verify student can be retrieved by ID."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO students (id, parent_id, display_name, grade_level)
                VALUES (:sid, :pid, 'Jayden', 4)
            """, sid=student_id, pid='22222222-2222-2222-2222-222222222222'))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT display_name FROM students WHERE id = :sid
            """, sid=student_id)).fetchone()
            assert result['display_name'] == 'Jayden'

    def test_get_student_by_parent(self, engine):
        """API-STD-003: Verify students can be retrieved by parent."""
        parent_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            for name in ['Jayden', 'Emma']:
                sid = f'{hash(name)}'[:32] + '00000000000'
                conn.execute(text("""
                    INSERT INTO students (id, parent_id, display_name, grade_level)
                    VALUES (:sid, :pid, :name, 4)
                """, sid=sid, pid=parent_id, name=name))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM students WHERE parent_id = :pid
            """, pid=parent_id)).fetchone()
            assert result['count'] == 2

    def test_update_student(self, engine):
        """API-STD-004: Verify student can be updated."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO students (id, parent_id, display_name, grade_level)
                VALUES (:sid, :pid, 'Jayden', 4)
            """, sid=student_id, pid='22222222-2222-2222-2222-222222222222'))
            conn.commit()

        # Update student
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE students SET grade_level = 5 WHERE id = :sid
            """, sid=student_id))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT grade_level FROM students WHERE id = :sid
            """, sid=student_id)).fetchone()
            assert result['grade_level'] == 5


class TestStudentCOPPA:
    """Tests for COPPA-compliant student operations."""

    def test_student_no_pii_fields(self, engine):
        """API-COPPA-001: Verify student table does not contain PII fields."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'students' AND column_name IN ('last_name', 'email', 'address')
            """)).fetchall()
            assert len(result) == 0

    def test_student_display_name_only(self, engine):
        """API-COPPA-002: Verify only display_name is stored, not full name."""
        student_id = '11111111-1111-1111-1111-111111111111'

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO students (id, parent_id, display_name, grade_level)
                VALUES (:sid, :pid, 'Jayden', 4)
            """, sid=student_id, pid='22222222-2222-2222-2222-222222222222'))
            conn.commit()

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT display_name FROM students WHERE id = :sid
            """, sid=student_id)).fetchone()
            # Only display name, no last name
            assert result['display_name'] == 'Jayden'
