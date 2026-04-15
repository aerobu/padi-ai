"""
Performance Benchmark: Question Load
====================================

Purpose: Verify question retrieval and loading performance meets SLA.

Target Metrics:
- Single question retrieval: < 10ms
- Question pool load (100 questions): < 100ms
- Vector similarity search: < 50ms
- Trigram similarity search: < 30ms

References:
- ENG-001-stage1.md (lines 1720-1760) - Question bank performance
- 10-lifecycle-stage1.md (lines 2500-2550) - Question load benchmarks
"""

import pytest
import time
import statistics
from typing import List, Dict, Any
from sqlalchemy import text


class TestQuestionRetrievalPerformance:
    """Performance tests for question retrieval."""

    def test_single_question_retrieval_under_10ms(self, engine):
        """PERF-201: Single question retrieval must complete in < 10ms."""
        # Ensure data exists
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO questions (
                    standard_code, difficulty, irt_difficulty, irt_discrimination, irt_guessing,
                    question_type, stem, options, correct_answer, source, status
                ) VALUES (
                    '4.QUICK.GET', 3, 0.150, 1.200, 0.2500,
                    'multiple_choice', 'Test question stem',
                    '[{"key": "A", "text": "1"}, {"key": "B", "text": "2"}]',
                    'A', 'seed', 'active'
                )
                ON CONFLICT (standard_code) DO UPDATE SET status = 'active'
            """))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM questions
                    WHERE standard_code = '4.QUICK.GET'
                """))
                question = result.fetchone()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average question retrieval time: {avg_time:.2f}ms")
        print(f"P99 retrieval time: {p99_time:.2f}ms")

        assert avg_time < 10, f"Average question retrieval time {avg_time:.2f}ms exceeds 10ms SLA"
        assert p99_time < 25, f"P99 retrieval time {p99_time:.2f}ms exceeds 25ms SLA"

    def test_question_pool_load_under_100ms(self, engine):
        """PERF-202: Question pool load (100 questions) must complete in < 100ms."""
        # Create question pool
        with engine.connect() as conn:
            for i in range(100):
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, irt_difficulty, irt_discrimination, irt_guessing,
                        question_type, stem, options, correct_answer, source, status
                    ) VALUES (
                        '4.POOL.Q{:03d}', 3, 0.150, 1.200, 0.2500,
                        'multiple_choice', 'Pool question {}'.format(i),
                        '[{"key": "A", "text": "1"}]',
                        'A', 'seed', 'active'
                    )
                    ON CONFLICT (standard_code) DO UPDATE SET status = 'active'
                """.format(i=i)))
            conn.commit()

        # Benchmark
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM questions
                    WHERE difficulty BETWEEN 3 AND 3
                    AND status = 'active'
                    LIMIT 100
                """))
                questions = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average pool load time: {avg_time:.2f}ms")
        print(f"Loaded {len(questions)} questions")
        print(f"P99 load time: {p99_time:.2f}ms")

        assert avg_time < 100, f"Average pool load time {avg_time:.2f}ms exceeds 100ms SLA"
        assert p99_time < 200, f"P99 load time {p99_time:.2f}ms exceeds 200ms SLA"

    def test_question_filter_by_standard_under_20ms(self, engine):
        """PERF-203: Filter questions by standard must complete in < 20ms."""
        # Create questions for specific standard
        with engine.connect() as conn:
            for i in range(50):
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status
                    ) VALUES (
                        '4.FILTER.STD', 3, 'multiple_choice',
                        'Filter question {}'.format(i),
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
                    SELECT * FROM questions
                    WHERE standard_code = '4.FILTER.STD'
                    AND status = 'active'
                """))
                questions = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average filter time: {avg_time:.2f}ms")
        print(f"Retrieved {len(questions)} questions")
        print(f"P99 filter time: {p99_time:.2f}ms")

        assert avg_time < 20, f"Average filter time {avg_time:.2f}ms exceeds 20ms SLA"
        assert p99_time < 50, f"P99 filter time {p99_time:.2f}ms exceeds 50ms SLA"


class TestVectorSearchPerformance:
    """Performance tests for vector similarity search."""

    def test_vector_similarity_search_under_50ms(self, engine):
        """PERF-204: Vector similarity search must complete in < 50ms."""
        # Create test data with embeddings
        with engine.connect() as conn:
            for i in range(100):
                vec = "[0.{:d}, 0.{:d}, 0.{:d}, 0.{:d}, 0.{:d}]".format(
                    (i * 7) % 10, (i * 3) % 10, (i * 5) % 10, (i * 2) % 10, (i * 9) % 10
                )
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status, content_embedding
                    ) VALUES (
                        '4.VECTOR.Q{:03d}', 3, 'multiple_choice',
                        'Vector question {}'.format(i),
                        '[{"key": "A", "text": "1"}]',
                        'A', 'seed', 'active', :vec
                    )
                    ON CONFLICT (standard_code) DO NOTHING
                """, vec=vec))
            conn.commit()

        # Benchmark
        query_vec = "[0.5, 0.5, 0.5, 0.5, 0.5]"

        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT standard_code, content_embedding <-> :query_vec as similarity
                    FROM questions
                    WHERE status = 'active'
                    ORDER BY similarity
                    LIMIT 10
                """, query_vec=query_vec))
                results = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average vector search time: {avg_time:.2f}ms")
        print(f"Found {len(results)} similar questions")
        print(f"P99 search time: {p99_time:.2f}ms")

        assert avg_time < 50, f"Average vector search time {avg_time:.2f}ms exceeds 50ms SLA"
        assert p99_time < 100, f"P99 search time {p99_time:.2f}ms exceeds 100ms SLA"

    def test_vector_deduplication_under_100ms(self, engine):
        """PERF-205: Question deduplication using vector similarity must complete in < 100ms."""
        # Create test questions
        with engine.connect() as conn:
            # Original question
            conn.execute(text("""
                INSERT INTO questions (
                    standard_code, difficulty, question_type, stem, options,
                    correct_answer, source, status, content_embedding
                ) VALUES (
                    '4.DEDUP.ORIG', 3, 'multiple_choice',
                    'Original question about fractions',
                    '[{"key": "A", "text": "1/2"}, {"key": "B", "text": "1/3"}]',
                    'A', 'seed', 'active', '[0.5, 0.5, 0.5, 0.5, 0.5]'
                )
            """))

            # Similar questions
            for i in range(50):
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status, content_embedding
                    ) VALUES (
                        '4.DEDUP.SIM{:03d}', 3, 'multiple_choice',
                        'Similar fraction question {}'.format(i),
                        '[{"key": "A", "text": "1/2"}]',
                        'A', 'ai_generated', 'active',
                        '[0.5{:d}, 0.5{:d}, 0.5{:d}, 0.5{:d}, 0.5{:d}]'
                    )
                    ON CONFLICT (standard_code) DO NOTHING
                """.format(i=i, i=i, i=i, i=i, i=i)))
            conn.commit()

        # Benchmark deduplication
        times = []
        for _ in range(5):
            start = time.perf_counter()

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT q1.standard_code, q2.standard_code,
                           q1.content_embedding <-> q2.content_embedding as similarity
                    FROM questions q1
                    JOIN questions q2 ON q1.standard_code < q2.standard_code
                    WHERE q1.standard_code = '4.DEDUP.ORIG'
                      AND q1.content_embedding <-> q2.content_embedding < 0.3
                """))
                duplicates = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average deduplication time: {avg_time:.2f}ms")
        print(f"Found {len(duplicates)} potential duplicates")
        print(f"P99 deduplication time: {p99_time:.2f}ms")

        assert avg_time < 100, f"Average deduplication time {avg_time:.2f}ms exceeds 100ms SLA"
        assert p99_time < 200, f"P99 deduplication time {p99_time:.2f}ms exceeds 200ms SLA"


class TestTrigramSearchPerformance:
    """Performance tests for trigram full-text search."""

    def test_trigram_similarity_search_under_30ms(self, engine):
        """PERF-206: Trigram similarity search must complete in < 30ms."""
        # Create test questions
        with engine.connect() as conn:
            for i in range(100):
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status
                    ) VALUES (
                        '4.TRIG.Q{:03d}', 3, 'multiple_choice',
                        'Math question about multiplication'.format(i),
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
                    SELECT standard_code, stem,
                           stem % 'math question multiplication' as similarity
                    FROM questions
                    WHERE stem % 'math question multiplication'
                      AND stem <-> 'math question multiplication' < 0.7
                    ORDER BY similarity DESC
                    LIMIT 10
                """))
                results = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average trigram search time: {avg_time:.2f}ms")
        print(f"Found {len(results)} similar questions")
        print(f"P99 search time: {p99_time:.2f}ms")

        assert avg_time < 30, f"Average trigram search time {avg_time:.2f}ms exceeds 30ms SLA"
        assert p99_time < 75, f"P99 search time {p99_time:.2f}ms exceeds 75ms SLA"

    def test_full_text_search_under_50ms(self, engine):
        """PERF-207: Full-text search on question stems must complete in < 50ms."""
        # Create test questions with varied text
        with engine.connect() as conn:
            for i in range(100):
                conn.execute(text("""
                    INSERT INTO questions (
                        standard_code, difficulty, question_type, stem, options,
                        correct_answer, source, status
                    ) VALUES (
                        '4.FULLTEXT.Q{:03d}', 3, 'multiple_choice',
                        'Calculate the product of {} and {}'.format(i+1, i+2),
                        '[{"key": "A", "text": "result"}]',
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
                    SELECT standard_code, stem
                    FROM questions
                    WHERE stem % 'calculate product'
                    ORDER BY stem % 'calculate product' DESC
                    LIMIT 20
                """))
                results = result.fetchall()

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average full-text search time: {avg_time:.2f}ms")
        print(f"Found {len(results)} matching questions")
        print(f"P99 search time: {p99_time:.2f}ms")

        assert avg_time < 50, f"Average full-text search time {avg_time:.2f}ms exceeds 50ms SLA"
        assert p99_time < 100, f"P99 search time {p99_time:.2f}ms exceeds 100ms SLA"
