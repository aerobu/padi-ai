"""
Performance Benchmark: Database Queries
======================================

Purpose: Verify database query performance meets SLA for all critical operations.

Target Metrics:
- CRUD operations: < 10ms per operation
- Join queries: < 50ms
- Aggregation queries: < 100ms
- Complex report queries: < 200ms

References:
- ENG-001-stage1.md (lines 1760-1800) - Database performance requirements
- 10-lifecycle-stage1.md (lines 2550-2600) - Query benchmarks
"""

import pytest
import time
import statistics
from typing import List, Dict, Any
from sqlalchemy import text, func


class TestCRUDPerformance:
    """Performance tests for CRUD operations."""

    def test_insert_under_10ms(self, engine):
        """PERF-301: Single row INSERT must complete in < 10ms."""
        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()

            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status, content_embedding
                    ) VALUES (
                        '4.CRUD.INS{:04d}', 3, 'multiple_choice',
                        'Insert test question',
                        '[{"key": "A", "text": "1"}]',
                        'A', 'seed', 'active', '[0.5, 0.5, 0.5, 0.5, 0.5]'
                    )
                    ON CONFLICT (standard_code) DO UPDATE SET
                        difficulty = 3,
                        updated_at = CURRENT_TIMESTAMP
                """.format(i=)))
                conn.commit()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average INSERT time: {avg_time:.2f}ms")
        print(f"P99 INSERT time: {p99_time:.2f}ms")

        assert avg_time < 10, f"Average INSERT time {avg_time:.2f}ms exceeds 10ms SLA"
        assert p99_time < 25, f"P99 INSERT time {p99_time:.2f}ms exceeds 25ms SLA"

    def test_select_under_10ms(self, engine):
        """PERF-302: Single row SELECT must complete in < 10ms."""
        # Ensure data exists
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (
                    standard_code, difficulty, question_type, stem, options,
                    correct_answer, source, status, content_embedding
                ) VALUES (
                    '4.CRUD.SEL', 3, 'multiple_choice',
                    'Select test question',
                    '[{"key": "A", "text": "1"}]',
                    'A', 'seed', 'active', '[0.5, 0.5, 0.5, 0.5, 0.5]'
                )
                ON CONFLICT (standard_code) DO NOTHING
            """))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM questions
                    WHERE standard_code = '4.CRUD.SEL'
                """))
                question = result.fetchone()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average SELECT time: {avg_time:.2f}ms")
        print(f"P99 SELECT time: {p99_time:.2f}ms")

        assert avg_time < 10, f"Average SELECT time {avg_time:.2f}ms exceeds 10ms SLA"
        assert p99_time < 25, f"P99 SELECT time {p99_time:.2f}ms exceeds 25ms SLA"

    def test_update_under_10ms(self, engine):
        """PERF-303: Single row UPDATE must complete in < 10ms."""
        # Ensure data exists
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (
                    standard_code, difficulty, question_type, stem, options,
                    correct_answer, source, status, content_embedding
                ) VALUES (
                    '4.CRUD.UPD', 3, 'multiple_choice',
                    'Update test question',
                    '[{"key": "A", "text": "1"}]',
                    'A', 'seed', 'active', '[0.5, 0.5, 0.5, 0.5, 0.5]'
                )
                ON CONFLICT (standard_code) DO NOTHING
            """))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()

            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE questions
                    SET difficulty = 4,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE standard_code = '4.CRUD.UPD'
                """))
                conn.commit()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average UPDATE time: {avg_time:.2f}ms")
        print(f"P99 UPDATE time: {p99_time:.2f}ms")

        assert avg_time < 10, f"Average UPDATE time {avg_time:.2f}ms exceeds 10ms SLA"
        assert p99_time < 25, f"P99 UPDATE time {p99_time:.2f}ms exceeds 25ms SLA"

    def test_delete_under_10ms(self, engine):
        """PERF-304: Single row DELETE must complete in < 10ms."""
        # Ensure data exists
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (
                    standard_code, difficulty, question_type, stem, options,
                    correct_answer, source, status, content_embedding
                ) VALUES (
                    '4.CRUD.DEL', 3, 'multiple_choice',
                    'Delete test question',
                    '[{"key": "A", "text": "1"}]',
                    'A', 'seed', 'active', '[0.5, 0.5, 0.5, 0.5, 0.5]'
                )
                ON CONFLICT (standard_code) DO NOTHING
            """))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()

            with engine.connect() as conn:
                conn.execute(text("""
                    DELETE FROM questions
                    WHERE standard_code = '4.CRUD.DEL'
                """))
                conn.commit()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average DELETE time: {avg_time:.2f}ms")
        print(f"P99 DELETE time: {p99_time:.2f}ms")

        assert avg_time < 10, f"Average DELETE time {avg_time:.2f}ms exceeds 10ms SLA"
        assert p99_time < 25, f"P99 DELETE time {p99_time:.2f}ms exceeds 25ms SLA"


class TestJoinQueryPerformance:
    """Performance tests for JOIN queries."""

    def test_question_standard_join_under_50ms(self, engine):
        """PERF-305: Question-Standard join must complete in < 50ms."""
        # Create test data
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO standards (
                    code, grade_level, domain, cluster, title, description
                ) VALUES (
                    '4.JOIN.STD', 4, 'OA', 'A', 'Join test standard', 'Test description'
                )
                ON CONFLICT (code) DO NOTHING
            """))

            for i in range(50):
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status
                    ) VALUES (
                        '4.JOIN.STD', 3, 'multiple_choice',
                        'Join question {}'.format(i),
                        '[{"key": "A", "text": "1"}]',
                        'A', 'seed', 'active'
                    )
                    ON CONFLICT (standard_code) DO NOTHING
                """.format(i=i)))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT s.code, s.title, q.id, q.stem
                    FROM standards s
                    LEFT JOIN questions q ON s.code = q.standard_code
                    WHERE s.code = '4.JOIN.STD'
                """))
                results = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average join time: {avg_time:.2f}ms")
        print(f"Retrieved {len(results)} rows")
        print(f"P99 join time: {p99_time:.2f}ms")

        assert avg_time < 50, f"Average join time {avg_time:.2f}ms exceeds 50ms SLA"
        assert p99_time < 100, f"P99 join time {p99_time:.2f}ms exceeds 100ms SLA"

    def test_assessment_student_join_under_50ms(self, engine):
        """PERF-306: Assessment-Student join must complete in < 50ms."""
        # Create test data
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO students (
                    id, parent_id, grade_level, display_name, avatar_id
                ) VALUES (
                    '4.JOIN.STUDENT', 'parent-123', 4, 'Test Student', 'avatar-1'
                )
                ON CONFLICT (id) DO NOTHING
            """))

            for i in range(100):
                conn.execute(text("""
                    INSERT INTO assessments (
                        student_id, assessment_type, status, total_questions,
                        completed_questions, score
                    ) VALUES (
                        '4.JOIN.STUDENT', 'diagnostic',
                        CASE WHEN {:d} % 2 = 0 THEN 'in_progress' ELSE 'completed' END,
                        35, {:d}, 70.0
                    )
                    ON CONFLICT (id) DO UPDATE SET status = 'in_progress'
                """.format(i=i, i=i)))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT s.display_name, s.grade_level,
                           a.assessment_id, a.status, a.score
                    FROM students s
                    JOIN assessments a ON s.id = a.student_id
                    WHERE s.id = '4.JOIN.STUDENT'
                    ORDER BY a.created_at DESC
                """))
                results = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average assessment join time: {avg_time:.2f}ms")
        print(f"Retrieved {len(results)} assessments")
        print(f"P99 join time: {p99_time:.2f}ms")

        assert avg_time < 50, f"Average assessment join time {avg_time:.2f}ms exceeds 50ms SLA"
        assert p99_time < 100, f"P99 join time {p99_time:.2f}ms exceeds 100ms SLA"

    def test_prerequisite_join_under_50ms(self, engine):
        """PERF-307: Prerequisite relationship join must complete in < 50ms."""
        # Create test data
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO standards (
                    code, grade_level, domain, cluster, title, description
                ) VALUES
                    ('4.PRI.MAIN', 4, 'OA', 'A', 'Main standard', 'Main'),
                    ('4.PRI.PREREQ1', 3, 'OA', 'A', 'Prereq 1', 'First'),
                    ('4.PRI.PREREQ2', 3, 'OA', 'A', 'Prereq 2', 'Second')
                ON CONFLICT (code) DO NOTHING
            """))

            conn.execute(text("""
                INSERT INTO prerequisite_relationships (standard_id, prerequisite_id)
                SELECT
                    (SELECT id FROM standards WHERE code = '4.PRI.MAIN'),
                    (SELECT id FROM standards WHERE code = '4.PRI.PREREQ1')
                ON CONFLICT DO NOTHING
            """))
            conn.execute(text("""
                INSERT INTO prerequisite_relationships (standard_id, prerequisite_id)
                SELECT
                    (SELECT id FROM standards WHERE code = '4.PRI.MAIN'),
                    (SELECT id FROM standards WHERE code = '4.PRI.PREREQ2')
                ON CONFLICT DO NOTHING
            """))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT main.code as main_standard,
                           prereq.code as prerequisite,
                           main.title as main_title
                    FROM prerequisite_relationships pr
                    JOIN standards main ON pr.standard_id = main.id
                    JOIN standards prereq ON pr.prerequisite_id = prereq.id
                    WHERE main.code = '4.PRI.MAIN'
                """))
                results = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average prerequisite join time: {avg_time:.2f}ms")
        print(f"Found {len(results)} prerequisites")
        print(f"P99 join time: {p99_time:.2f}ms")

        assert avg_time < 50, f"Average prerequisite join time {avg_time:.2f}ms exceeds 50ms SLA"
        assert p99_time < 100, f"P99 join time {p99_time:.2f}ms exceeds 100ms SLA"


class TestAggregationPerformance:
    """Performance tests for aggregation queries."""

    def test_question_count_aggregation_under_50ms(self, engine):
        """PERF-308: Question count aggregation must complete in < 50ms."""
        # Create test data
        with engine.connect() as conn:
            for i in range(500):
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status
                    ) VALUES (
                        '4.AGG.Q{:04d}', {:d}, 'multiple_choice',
                        'Aggregation question {}'.format(i, (i % 5) + 1),
                        '[{"key": "A", "text": "1"}]',
                        'A', 'seed', 'active'
                    )
                    ON CONFLICT (standard_code) DO NOTHING
                """.format(i=i)))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT standard_code, COUNT(*) as question_count,
                           AVG(difficulty) as avg_difficulty,
                           MAX(irt_difficulty) as max_irt
                    FROM questions
                    WHERE status = 'active'
                    GROUP BY standard_code
                """))
                results = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average aggregation time: {avg_time:.2f}ms")
        print(f"Aggregated {len(results)} standards")
        print(f"P99 aggregation time: {p99_time:.2f}ms")

        assert avg_time < 50, f"Average aggregation time {avg_time:.2f}ms exceeds 50ms SLA"
        assert p99_time < 100, f"P99 aggregation time {p99_time:.2f}ms exceeds 100ms SLA"

    def test_skill_state_aggregation_under_100ms(self, engine):
        """PERF-309: Skill state aggregation for dashboard must complete in < 100ms."""
        # Create test data
        with engine.connect() as conn:
            for i in range(200):
                conn.execute(text("""
                    INSERT INTO student_skill_states (
                        student_id, standard_code, p_mastery, p_transit, p_slip, p_guess,
                        mastery_level, total_attempts, total_correct
                    ) VALUES (
                        '4.AGG.STUDENT',
                        '4.AGG.SKILL{:04d}',
                        0.{:02d}, 0.1, 0.05, 0.25,
                        CASE
                            WHEN {:d} > 80 THEN 'mastered'
                            WHEN {:d} > 60 THEN 'on_par'
                            WHEN {:d} > 40 THEN 'below_par'
                            ELSE 'not_assessed'
                        END,
                        {:d}, {:d}
                    )
                    ON CONFLICT (student_id, standard_code) DO UPDATE SET
                        p_mastery = 0.{:02d}
                """.format(i=i, (i * 5) % 100, (i * 5) % 100, (i * 5) % 100, (i * 5) % 100, i, (i * 3) % 100, (i * 5) % 100)))
            conn.commit()

        # Benchmark dashboard query
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total_standards,
                        SUM(CASE WHEN mastery_level = 'mastered' THEN 1 ELSE 0 END) as mastered,
                        SUM(CASE WHEN mastery_level = 'on_par' THEN 1 ELSE 0 END) as on_par,
                        SUM(CASE WHEN mastery_level = 'below_par' THEN 1 ELSE 0 END) as below_par,
                        SUM(CASE WHEN mastery_level = 'not_assessed' THEN 1 ELSE 0 END) as not_assessed,
                        AVG(p_mastery) as avg_mastery
                    FROM student_skill_states
                    WHERE student_id = '4.AGG.STUDENT'
                """))
                result = result.fetchone()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average dashboard aggregation time: {avg_time:.2f}ms")
        print(f"Mastery: {result['mastered']} mastered, {result['on_par']} on-par, {result['below_par']} below-par")
        print(f"P99 time: {p99_time:.2f}ms")

        assert avg_time < 100, f"Average dashboard aggregation time {avg_time:.2f}ms exceeds 100ms SLA"
        assert p99_time < 200, f"P99 dashboard time {p99_time:.2f}ms exceeds 200ms SLA"

    def test_assessment_statistics_under_100ms(self, engine):
        """PERF-310: Assessment statistics aggregation must complete in < 100ms."""
        # Create test data
        with engine.connect() as conn:
            for i in range(500):
                conn.execute(text("""
                    INSERT INTO assessments (
                        student_id, assessment_type, status, total_questions,
                        completed_questions, score
                    ) VALUES (
                        '4.AGG.STUDENT', 'diagnostic',
                        CASE WHEN {:d} % 3 = 0 THEN 'completed' ELSE 'in_progress' END,
                        35,
                        CASE WHEN {:d} % 2 = 0 THEN 35 ELSE {:d} END,
                        CASE
                            WHEN {:d} % 10 = 0 THEN 95.0
                            WHEN {:d} % 10 < 5 THEN 70.0
                            ELSE 50.0
                        END
                    )
                    ON CONFLICT (id) DO UPDATE SET score = 70.0
                """.format(i=i, i, i % 35, i % 100, i % 100)))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total_assessments,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        AVG(score) as avg_score,
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        AVG((completed_questions::float / total_questions) * 100) as completion_rate
                    FROM assessments
                    WHERE student_id = '4.AGG.STUDENT'
                      AND assessment_type = 'diagnostic'
                """))
                result = result.fetchone()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average assessment statistics time: {avg_time:.2f}ms")
        print(f"Completed: {result['completed']}/{result['total_assessments']}, Avg score: {result['avg_score']:.1f}")
        print(f"P99 time: {p99_time:.2f}ms")

        assert avg_time < 100, f"Average assessment statistics time {avg_time:.2f}ms exceeds 100ms SLA"
        assert p99_time < 200, f"P99 statistics time {p99_time:.2f}ms exceeds 200ms SLA"


class TestReportQueryPerformance:
    """Performance tests for complex report queries."""

    def test_student_performance_report_under_200ms(self, engine):
        """PERF-311: Student performance report must complete in < 200ms."""
        # Create comprehensive test data
        with engine.connect() as conn:
            # Create student
            conn.execute(text("""
                INSERT INTO students (
                    id, parent_id, grade_level, display_name, avatar_id
                ) VALUES (
                    '4.REPORT.STUDENT', 'parent-123', 4, 'Report Student', 'avatar-1'
                )
                ON CONFLICT (id) DO NOTHING
            """))

            # Create standards
            for domain in ['OA', 'NBT', 'NF', 'MD']:
                for i in range(3):
                    conn.execute(text("""
                        INSERT INTO standards (
                            code, grade_level, domain, cluster, title, description
                        ) VALUES (
                            '4.REP.{:s}.{:d}', 4, '{:s}', '{:s}',
                            'Report standard', 'Test'
                        )
                        ON CONFLICT (code) DO NOTHING
                    """.format(domain, i, domain, domain[0])))

            # Create skill states
            for domain in ['OA', 'NBT', 'NF', 'MD']:
                for i in range(3):
                    code = '4.REP.{}.{:d}'.format(domain, i)
                    conn.execute(text("""
                        INSERT INTO student_skill_states (
                            student_id, standard_code, p_mastery, mastery_level,
                            total_attempts, total_correct
                        ) VALUES (
                            '4.REPORT.STUDENT', '{:s}', 0.{:d},
                            CASE WHEN {:d} > 70 THEN 'on_par' ELSE 'below_par' END,
                            {:d}, {:d}
                        )
                        ON CONFLICT (student_id, standard_code) DO UPDATE SET
                            p_mastery = 0.{:d}
                    """.format(code, (i * 20) % 100, (i * 20) % 100, i * 10, i * 5, (i * 20) % 100)))
            conn.commit()

        # Benchmark complex report query
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        s.display_name,
                        s.grade_level,
                        COUNT(DISTINCT ss.standard_code) as standards_tracked,
                        SUM(CASE WHEN ss.mastery_level = 'mastered' THEN 1 ELSE 0 END) as mastered,
                        SUM(CASE WHEN ss.mastery_level = 'on_par' THEN 1 ELSE 0 END) as on_par,
                        SUM(CASE WHEN ss.mastery_level = 'below_par' THEN 1 ELSE 0 END) as below_par,
                        AVG(ss.p_mastery) * 100 as avg_mastery_percent,
                        SUM(ss.total_attempts) as total_attempts,
                        SUM(ss.total_correct) as total_correct,
                        ROUND((SUM(ss.total_correct)::numeric / NULLIF(SUM(ss.total_attempts), 0) * 100), 2) as accuracy_percent,
                        STRING_AGG(DISTINCT st.domain, ', ') as domains_covered
                    FROM students s
                    LEFT JOIN student_skill_states ss ON s.id = ss.student_id
                    LEFT JOIN standards st ON ss.standard_code = st.code
                    WHERE s.id = '4.REPORT.STUDENT'
                    GROUP BY s.id, s.display_name, s.grade_level
                """))
                report = result.fetchone()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average report query time: {avg_time:.2f}ms")
        print(f"Report: {report['standards_tracked']} standards, {report['avg_mastery_percent']:.1f}% mastery")
        print(f"P99 report time: {p99_time:.2f}ms")

        assert avg_time < 200, f"Average report query time {avg_time:.2f}ms exceeds 200ms SLA"
        assert p99_time < 400, f"P99 report time {p99_time:.2f}ms exceeds 400ms SLA"
