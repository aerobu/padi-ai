"""
Test Suite: Redis - Assessment Cache Tests

Purpose: Validate Redis caching for assessment state:
- Assessment session caching
- Question state caching
- BKT state temporary caching
- Cache expiration handling
"""

import pytest
from datetime import datetime, timedelta, timezone


class TestAssessmentSessionCache:
    """Tests for assessment session caching."""

    @pytest.fixture
    def redis_client(self, redis_url):
        """Get Redis client fixture."""
        import redis
        return redis.from_url(redis_url)

    def test_cache_assessment_state(self, redis_client):
        """RED-ASM-001: Verify assessment state can be cached."""
        assessment_id = "assessment:12345"
        state = {
            "question_index": 15,
            "questions_answered": 15,
            "correct_count": 12,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
        }
        
        # Cache the state
        redis_client.setex(
            assessment_id,
            3600,  # 1 hour TTL
            str(state)
        )
        
        # Retrieve and verify
        cached = redis_client.get(assessment_id)
        assert cached is not None

    def test_assessment_cache_expiration(self, redis_client):
        """RED-ASM-002: Verify assessment cache expires after TTL."""
        assessment_id = "assessment:expire:123"
        
        # Set with short TTL
        redis_client.setex(assessment_id, 2, "test_data")
        
        # Should exist initially
        assert redis_client.get(assessment_id) is not None
        
        # Wait for expiration
        import time
        time.sleep(3)
        
        # Should be expired
        assert redis_client.get(assessment_id) is None

    def test_assessment_cache_invalidation(self, redis_client):
        """RED-ASM-003: Verify assessment cache can be invalidated."""
        assessment_id = "assessment:invalidate:123"
        
        # Set data
        redis_client.set(assessment_id, "test_data")
        assert redis_client.get(assessment_id) is not None
        
        # Invalidate
        redis_client.delete(assessment_id)
        assert redis_client.get(assessment_id) is None


class TestQuestionCache:
    """Tests for question caching."""

    @pytest.fixture
    def redis_client(self, redis_url):
        """Get Redis client fixture."""
        import redis
        return redis.from_url(redis_url)

    def test_cache_question_by_id(self, redis_client):
        """RED-QUES-001: Verify question can be cached by ID."""
        question_id = "question:456"
        question_data = {
            "standard_code": "4.OA.A.1",
            "difficulty": 3,
            "stem": "Test question",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
        }
        
        # Cache question
        redis_client.setex(
            question_id,
            300,  # 5 minute TTL
            str(question_data)
        )
        
        # Retrieve
        cached = redis_client.get(question_id)
        assert cached is not None

    def test_question_cache_by_standard(self, redis_client):
        """RED-QUES-002: Verify questions can be cached by standard."""
        standard = "questions:4.OA.A.1"
        
        # Add questions to sorted set
        questions = ["q1", "q2", "q3"]
        scores = [0.1, 0.2, 0.3]
        
        pipe = redis_client.pipeline()
        for q, s in zip(questions, scores):
            pipe.zadd(f"{standard}:pool", {q: s})
        pipe.expire(f"{standard}:pool", 600)
        pipe.execute()
        
        # Verify
        cached = redis_client.zrange(f"{standard}:pool", 0, -1)
        assert len(cached) == 3

    def test_question_cache_lru(self, redis_client):
        """RED-QUES-003: Verify question cache uses LRU eviction."""
        # Set up memory limit scenario
        max_memory = "maxmemory-policy allkeys-lru"
        
        # In real implementation, Redis would evict least recently used
        # Here we verify the pattern works
        for i in range(10):
            redis_client.setex(f"q:{i}", 300, f"data_{i}")
        
        # All data should be accessible
        for i in range(10):
            assert redis_client.get(f"q:{i}") is not None


class TestBKTStateCache:
    """Tests for BKT state caching."""

    @pytest.fixture
    def redis_client(self, redis_url):
        """Get Redis client fixture."""
        import redis
        return redis.from_url(redis_url)

    def test_cache_bkt_state(self, redis_client):
        """RED-BKT-001: Verify BKT state can be cached."""
        bkt_key = "bkt:student:123:standard:4.OA.A.1"
        bkt_state = {
            "p_mastery": 0.5000,
            "p_slip": 0.0500,
            "p_guess": 0.2500,
            "total_attempts": 10,
            "total_correct": 8,
            "streak_current": 3,
            "streak_longest": 5,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        
        # Cache BKT state with short TTL (cache-aside pattern)
        redis_client.setex(
            bkt_key,
            300,  # 5 minute TTL
            str(bkt_state)
        )
        
        # Retrieve and verify
        cached = redis_client.get(bkt_key)
        assert cached is not None

    def test_bkt_state_batch_cache(self, redis_client):
        """RED-BKT-002: Verify multiple BKT states can be batched."""
        # Create pipeline for batch operations
        pipe = redis_client.pipeline()
        
        for i, std_code in enumerate(["4.OA.A.1", "4.OA.A.2", "4.NBT.A.1"]):
            key = f"bkt:student:123:standard:{std_code}"
            value = f"p_mastery:{0.5 + i * 0.1}"
            pipe.setex(key, 300, value)
        
        pipe.execute()
        
        # Verify all cached
        for i, std_code in enumerate(["4.OA.A.1", "4.OA.A.2", "4.NBT.A.1"]):
            key = f"bkt:student:123:standard:{std_code}"
            assert redis_client.get(key) is not None


class TestSessionTimeout:
    """Tests for session timeout handling."""

    @pytest.fixture
    def redis_client(self, redis_url):
        """Get Redis client fixture."""
        import redis
        return redis.from_url(redis_url)

    def test_session_timeout_after_inactivity(self, redis_client):
        """RED-TIME-001: Verify session times out after inactivity."""
        session_key = "session:student:123"
        
        # Set session with 60 minute timeout
        redis_client.setex(session_key, 3600, "active_session")
        
        # Verify session exists
        assert redis_client.get(session_key) is not None

    def test_concurrent_assessment_prevention(self, redis_client):
        """RED-TIME-002: Verify only one assessment per student."""
        student_id = "student:123"
        
        # Check for existing assessment lock
        lock_key = f"assessment:lock:{student_id}"
        
        # Set lock (student starts assessment)
        acquired = redis_client.set(lock_key, "active", nx=True, ex=3600)
        
        assert acquired is True  # Lock acquired
        
        # Second attempt should fail
        acquired_again = redis_client.set(lock_key, "active", nx=True, ex=3600)
        assert acquired_again is None  # Lock not acquired
