"""
Performance Benchmark: BKT Computation
=======================================

Purpose: Verify that Bayesian Knowledge Tracing computations meet performance SLA.

Target Metrics:
- Single student skill state update: < 50ms
- Full diagnostic assessment (35 questions): < 2000ms
- BKT state calculation for 50 standards: < 500ms

References:
- ENG-001-stage1.md (lines 1640-1680) - BKT performance requirements
- 10-lifecycle-stage1.md (lines 2400-2450) - Performance benchmarks
"""

import pytest
import time
import statistics
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import BKT service
import sys
sys.path.insert(0, 'apps/api/src')

from services.bkt_service import BKTService
from repositories.student_skill_state_repository import StudentSkillStateRepository


class TestBKTComputationPerformance:
    """Performance tests for BKT computations."""

    @pytest.fixture
    def bkt_service(self, db_session: AsyncSession) -> BKTService:
        """Create BKT service instance."""
        skill_repo = StudentSkillStateRepository(db_session)
        return BKTService(skill_repo)

    @pytest.fixture
    def large_skill_state(self, engine) -> List[Dict[str, Any]]:
        """Create large dataset of skill states."""
        states = []
        for i in range(100):
            states.append({
                'student_id': 'perf-test-student',
                'standard_code': f'4.TEST.STD{i:03d}',
                'p_mastery': 0.1 + (i * 0.01),
                'p_transit': 0.1,
                'p_slip': 0.05,
                'p_guess': 0.25,
                'total_attempts': i * 2,
                'total_correct': i,
                'streak_current': i % 3,
                'streak_longest': i,
            })
        return states

    def test_single_skill_update_under_50ms(self, bkt_service, sample_skill_state):
        """PERF-001: Single skill state update must complete in < 50ms."""
        # Warm up
        for _ in range(3):
            await bkt_service.update_skill_state(
                student_id='12345678-1234-1234-1234-123456789012',
                standard_code='4.OA.A.1',
                is_correct=True
            )

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()
            await bkt_service.update_skill_state(
                student_id='12345678-1234-1234-1234-123456789012',
                standard_code='4.OA.A.1',
                is_correct=True
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        # Assert
        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"Average time: {avg_time:.2f}ms")
        print(f"Max time: {max_time:.2f}ms")

        assert avg_time < 50, f"Average BKT update time {avg_time:.2f}ms exceeds 50ms SLA"
        assert max_time < 100, f"Max BKT update time {max_time:.2f}ms exceeds 100ms threshold"

    def test_full_assessment_under_2000ms(self, bkt_service, large_skill_state):
        """PERF-002: Full diagnostic assessment BKT computation must complete in < 2000ms."""
        # Simulate 35 question assessment with BKT updates
        assessment_responses = [True, True, False, True, True, False, True, True, True, False] * 3 + [True, True, True]

        # Warm up
        for _ in range(3):
            for is_correct in assessment_responses[:5]:
                await bkt_service.update_skill_state(
                    student_id='perf-test-assessment',
                    standard_code='4.OA.A.1',
                    is_correct=is_correct
                )

        # Benchmark
        times = []
        for _ in range(5):
            start = time.perf_counter()

            for is_correct in assessment_responses:
                await bkt_service.update_skill_state(
                    student_id='perf-test-assessment',
                    standard_code='4.OA.A.1',
                    is_correct=is_correct
                )

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"Average assessment time: {avg_time:.2f}ms")
        print(f"Max assessment time: {max_time:.2f}ms")

        assert avg_time < 2000, f"Average assessment BKT time {avg_time:.2f}ms exceeds 2000ms SLA"
        assert max_time < 3000, f"Max assessment BKT time {max_time:.2f}ms exceeds 3000ms threshold"

    def test_50_standards_under_500ms(self, bkt_service):
        """PERF-003: BKT state calculation for 50 standards must complete in < 500ms."""
        standard_codes = [f'4.TEST.STD{i:03d}' for i in range(50)]

        # Warm up
        for _ in range(3):
            for code in standard_codes[:5]:
                await bkt_service.update_skill_state(
                    student_id='perf-test-standards',
                    standard_code=code,
                    is_correct=True
                )

        # Benchmark
        times = []
        for _ in range(5):
            start = time.perf_counter()

            for code in standard_codes:
                await bkt_service.update_skill_state(
                    student_id='perf-test-standards',
                    standard_code=code,
                    is_correct=True
                )

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"Average 50 standards time: {avg_time:.2f}ms")
        print(f"Max 50 standards time: {max_time:.2f}ms")

        assert avg_time < 500, f"Average 50 standards BKT time {avg_time:.2f}ms exceeds 500ms SLA"
        assert max_time < 1000, f"Max 50 standards BKT time {max_time:.2f}ms exceeds 1000ms threshold"

    def test_concurrent_bkt_computations(self, bkt_service):
        """PERF-004: Concurrent BKT computations for multiple students must maintain SLA."""
        student_ids = [f'student-{i}' for i in range(10)]
        standard_codes = ['4.OA.A.1', '4.OA.A.2', '4.OA.B.1']

        # Warm up
        for _ in range(3):
            for sid in student_ids[:3]:
                for code in standard_codes:
                    await bkt_service.update_skill_state(
                        student_id=sid,
                        standard_code=code,
                        is_correct=True
                    )

        # Benchmark concurrent updates
        times = []
        for _ in range(5):
            start = time.perf_counter()

            # Simulate concurrent updates (sequential in test, but measures throughput)
            for sid in student_ids:
                for code in standard_codes:
                    await bkt_service.update_skill_state(
                        student_id=sid,
                        standard_code=code,
                        is_correct=True
                    )

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        per_student_time = avg_time / len(student_ids)

        print(f"Total concurrent time: {avg_time:.2f}ms")
        print(f"Per-student time: {per_student_time:.2f}ms")

        assert per_student_time < 100, f"Per-student concurrent BKT time {per_student_time:.2f}ms exceeds 100ms SLA"

    def test_bkt_with_database_io(self, bkt_service, db_session):
        """PERF-005: BKT computation including database I/O must complete in < 100ms."""
        student_id = 'perf-test-db-io'
        standard_code = '4.OA.TEST.IO'

        # Warm up
        for _ in range(3):
            await bkt_service.update_skill_state(
                student_id=student_id,
                standard_code=standard_code,
                is_correct=True
            )

        # Benchmark with DB IO
        times = []
        for _ in range(5):
            start = time.perf_counter()

            await bkt_service.update_skill_state(
                student_id=student_id,
                standard_code=standard_code,
                is_correct=True
            )

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"Average BKT with DB IO: {avg_time:.2f}ms")
        print(f"Max BKT with DB IO: {max_time:.2f}ms")

        assert avg_time < 100, f"Average BKT with DB IO {avg_time:.2f}ms exceeds 100ms SLA"
        assert max_time < 200, f"Max BKT with DB IO {max_time:.2f}ms exceeds 200ms threshold"


class TestBKTStatePersistence:
    """Performance tests for BKT state persistence."""

    def test_batch_skill_state_update(self, engine):
        """PERF-006: Batch update of 100 skill states must complete in < 500ms."""
        with engine.connect() as conn:
            # Warm up
            for _ in range(3):
                conn.execute(text("""
                    INSERT INTO student_skill_states (
                        student_id, standard_code, p_mastery, p_transit, p_slip, p_guess,
                        total_attempts, total_correct
                    ) VALUES (
                        'batch-test', '4.BATCH.TEST', 0.5, 0.1, 0.05, 0.25, 10, 7
                    )
                    ON CONFLICT (student_id, standard_code) DO UPDATE SET
                        p_mastery = 0.5,
                        updated_at = CURRENT_TIMESTAMP
                """))
                conn.commit()

            # Benchmark batch update
            times = []
            for _ in range(5):
                start = time.perf_counter()

                conn.execute(text("""
                    UPDATE student_skill_states
                    SET p_mastery = 0.6,
                        total_attempts = total_attempts + 1,
                        total_correct = total_correct + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE student_id = 'batch-test'
                """))
                conn.commit()

                end = time.perf_counter()
                times.append((end - start) * 1000)

            # Assert
            avg_time = statistics.mean(times)

            print(f"Average batch update time: {avg_time:.2f}ms")

            assert avg_time < 500, f"Average batch update time {avg_time:.2f}ms exceeds 500ms SLA"

    def test_skill_state_query_performance(self, engine):
        """PERF-007: Query for student's 100 skill states must complete in < 100ms."""
        with engine.connect() as conn:
            # Ensure data exists
            for i in range(100):
                conn.execute(text("""
                    INSERT INTO student_skill_states (
                        student_id, standard_code, p_mastery, p_transit, p_slip, p_guess
                    ) VALUES (
                        'perf-query-test', '4.QUERY.STD{:03d}', 0.5, 0.1, 0.05, 0.25
                    )
                    ON CONFLICT (student_id, standard_code) DO NOTHING
                """.format(i=i)))
            conn.commit()

            # Benchmark query
            times = []
            for _ in range(5):
                start = time.perf_counter()

                result = conn.execute(text("""
                    SELECT * FROM student_skill_states
                    WHERE student_id = 'perf-query-test'
                """))
                states = result.fetchall()

                end = time.perf_counter()
                times.append((end - start) * 1000)

            # Assert
            avg_time = statistics.mean(times)

            print(f"Average skill state query time: {avg_time:.2f}ms")
            print(f"Retrieved {len(states)} states")

            assert avg_time < 100, f"Average skill state query time {avg_time:.2f}ms exceeds 100ms SLA"


class TestBKTCaching:
    """Performance tests for BKT state caching."""

    def test_bkt_state_cache_hit(self, bkt_service, db_session, redis_client):
        """PERF-008: Cached BKT state retrieval must complete in < 5ms."""
        student_id = 'perf-cache-test'
        standard_code = '4.OA.CACHE'

        # Pre-compute and cache state
        await bkt_service.update_skill_state(
            student_id=student_id,
            standard_code=standard_code,
            is_correct=True
        )

        # Benchmark cache hits
        times = []
        for _ in range(10):
            start = time.perf_counter()

            # Try to get from cache (implementation depends on caching layer)
            cache_key = f"bkt_state:{student_id}:{standard_code}"
            cached = await redis_client.get(cache_key)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)

        print(f"Average cache lookup time: {avg_time:.2f}ms")

        assert avg_time < 5, f"Average cache lookup time {avg_time:.2f}ms exceeds 5ms SLA"
