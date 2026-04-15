"""
Performance Benchmark: Assessment API
======================================

Purpose: Verify that assessment API endpoints meet performance SLA under load.

Target Metrics:
- Assessment start: < 200ms
- Question retrieval: < 100ms
- Answer submission: < 150ms
- 100 concurrent sessions: < 1s per request

References:
- ENG-001-stage1.md (lines 1680-1720) - API performance requirements
- 10-lifecycle-stage1.md (lines 2450-2500) - Load testing requirements
"""

import pytest
import time
import statistics
import random
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import text

# Import main app
import sys
sys.path.insert(0, 'apps/api/src')

from main import app


class TestAssessmentAPIPerformance:
    """Performance tests for assessment API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {
            "Authorization": "Bearer test_jwt_token_for_parent"
        }

    def test_assessment_start_under_200ms(self, client, auth_headers):
        """PERF-101: Assessment start must complete in < 200ms."""
        # Warm up
        for _ in range(3):
            response = client.post(
                "/api/v1/assessments/start",
                headers=auth_headers,
                json={"student_id": "test-student"}
            )

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()
            response = client.post(
                "/api/v1/assessments/start",
                headers=auth_headers,
                json={"student_id": "test-student"}
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average start time: {avg_time:.2f}ms")
        print(f"P99 start time: {p99_time:.2f}ms")

        assert avg_time < 200, f"Average assessment start time {avg_time:.2f}ms exceeds 200ms SLA"
        assert p99_time < 500, f"P99 assessment start time {p99_time:.2f}ms exceeds 500ms threshold"

    def test_question_retrieval_under_100ms(self, client, auth_headers):
        """PERF-102: Question retrieval must complete in < 100ms."""
        # Get assessment first
        assessment_response = client.post(
            "/api/v1/assessments/start",
            headers=auth_headers,
            json={"student_id": "test-student"}
        )
        assessment_id = assessment_response.json().get("assessment_id")

        # Benchmark question retrieval
        times = []
        for _ in range(10):
            start = time.perf_counter()
            response = client.get(
                f"/api/v1/assessments/{assessment_id}/questions/1",
                headers=auth_headers
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average question retrieval time: {avg_time:.2f}ms")
        print(f"P99 retrieval time: {p99_time:.2f}ms")

        assert avg_time < 100, f"Average question retrieval time {avg_time:.2f}ms exceeds 100ms SLA"
        assert p99_time < 250, f"P99 retrieval time {p99_time:.2f}ms exceeds 250ms threshold"

    def test_answer_submission_under_150ms(self, client, auth_headers):
        """PERF-103: Answer submission must complete in < 150ms."""
        # Get assessment
        assessment_response = client.post(
            "/api/v1/assessments/start",
            headers=auth_headers,
            json={"student_id": "test-student"}
        )
        assessment_id = assessment_response.json().get("assessment_id")

        # Benchmark answer submission
        times = []
        for _ in range(10):
            start = time.perf_counter()
            response = client.post(
                f"/api/v1/assessments/{assessment_id}/answers",
                headers=auth_headers,
                json={
                    "question_id": "q1",
                    "selected_option": "A",
                    "time_spent_seconds": 30
                }
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average answer submission time: {avg_time:.2f}ms")
        print(f"P99 submission time: {p99_time:.2f}ms")

        assert avg_time < 150, f"Average answer submission time {avg_time:.2f}ms exceeds 150ms SLA"
        assert p99_time < 300, f"P99 submission time {p99_time:.2f}ms exceeds 300ms threshold"

    def test_assessment_completion_under_500ms(self, client, auth_headers):
        """PERF-104: Assessment completion must complete in < 500ms."""
        # Start assessment
        assessment_response = client.post(
            "/api/v1/assessments/start",
            headers=auth_headers,
            json={"student_id": "test-student"}
        )
        assessment_id = assessment_response.json().get("assessment_id")

        # Answer all questions (35 questions)
        for i in range(1, 36):
            client.post(
                f"/api/v1/assessments/{assessment_id}/answers",
                headers=auth_headers,
                json={
                    "question_id": f"q{i}",
                    "selected_option": "A",
                    "time_spent_seconds": 30
                }
            )

        # Benchmark completion
        times = []
        for _ in range(5):
            start = time.perf_counter()
            response = client.post(
                f"/api/v1/assessments/{assessment_id}/complete",
                headers=auth_headers
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average completion time: {avg_time:.2f}ms")
        print(f"P99 completion time: {p99_time:.2f}ms")

        assert avg_time < 500, f"Average assessment completion time {avg_time:.2f}ms exceeds 500ms SLA"
        assert p99_time < 1000, f"P99 completion time {p99_time:.2f}ms exceeds 1000ms threshold"


class TestAssessmentConcurrency:
    """Performance tests for concurrent assessment sessions."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_100_concurrent_sessions(self, client):
        """PERF-105: 100 concurrent assessment sessions must maintain < 1s per request."""
        import concurrent.futures

        def start_assessment(session_id: int) -> float:
            """Start assessment and return timing."""
            headers = {"Authorization": f"Bearer test_token_{session_id}"}
            start = time.perf_counter()
            response = client.post(
                "/api/v1/assessments/start",
                headers=headers,
                json={"student_id": f"student-{session_id}"}
            )
            end = time.perf_counter()
            return (end - start) * 1000

        # Run 100 concurrent sessions
        times = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(start_assessment, i)
                for i in range(100)
            ]

            for future in concurrent.futures.as_completed(futures):
                times.append(future.result())

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]
        max_time = max(times)

        print(f"Average concurrent time: {avg_time:.2f}ms")
        print(f"P99 concurrent time: {p99_time:.2f}ms")
        print(f"Max concurrent time: {max_time:.2f}ms")

        assert avg_time < 500, f"Average concurrent time {avg_time:.2f}ms exceeds 500ms SLA"
        assert p99_time < 1000, f"P99 concurrent time {p99_time:.2f}ms exceeds 1000ms SLA"
        assert max_time < 2000, f"Max concurrent time {max_time:.2f}ms exceeds 2000ms threshold"

    def test_concurrent_answer_submissions(self, client):
        """PERF-106: Concurrent answer submissions must maintain < 200ms per request."""
        import concurrent.futures

        def submit_answer(session_id: int) -> float:
            """Submit answer and return timing."""
            headers = {"Authorization": f"Bearer test_token_{session_id}"}
            start = time.perf_counter()
            response = client.post(
                "/api/v1/assessments/test-assessment/answers",
                headers=headers,
                json={
                    "question_id": "q1",
                    "selected_option": "A",
                    "time_spent_seconds": 30
                }
            )
            end = time.perf_counter()
            return (end - start) * 1000

        # Run 50 concurrent submissions
        times = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(submit_answer, i)
                for i in range(50)
            ]

            for future in concurrent.futures.as_completed(futures):
                times.append(future.result())

        # Assert
        avg_time = statistics.mean(times)
        p99_time = sorted(times)[int(len(times) * 0.99)]

        print(f"Average submission time: {avg_time:.2f}ms")
        print(f"P99 submission time: {p99_time:.2f}ms")

        assert avg_time < 200, f"Average submission time {avg_time:.2f}ms exceeds 200ms SLA"
        assert p99_time < 500, f"P99 submission time {p99_time:.2f}ms exceeds 500ms SLA"
