"""
Test Suite: Redis - Question Cache Tests (Detailed)

Purpose: Validate question caching patterns and query patterns.
"""

import pytest
from datetime import datetime, timedelta, timezone


class TestQuestionPoolCache:
    """Tests for question pool caching."""

    @pytest.fixture
    def redis_client(self, redis_url):
        import redis
        return redis.from_url(redis_url)

    def test_dynamic_question_pool(self, redis_client):
        """RED-QPOOL-001: Verify dynamic question pool building."""
        pool_key = "pool:diagnostic:4.OA"
        
        # Build pool with scores (IRT-based selection)
        questions = [
            ("q1", 0.3),  # Good difficulty match
            ("q2", 0.7),  # Too hard
            ("q3", 0.5),  # Perfect match
        ]
        
        pipe = redis_client.pipeline()
        pipe.delete(pool_key)
        for q_id, score in questions:
            pipe.zadd(pool_key, {q_id: score})
        pipe.expire(pool_key, 1800)
        pipe.execute()
        
        # Retrieve top questions
        top_questions = redis_client.zrevrange(pool_key, 0, 10)
        assert len(top_questions) == 3

    def test_question_cache_warm_up(self, redis_client):
        """RED-QPOOL-002: Verify question cache can be warmed."""
        warmup_key = "warmup:standards:4.OA"
        
        # Warm up cache with frequently accessed standards
        standards = ["4.OA.A.1", "4.OA.A.2", "4.OA.B.1", "4.OA.C.1"]
        
        pipe = redis_client.pipeline()
        for std in standards:
            pipe.setex(f"standard:{std}", 3600, "cached_metadata")
        pipe.execute()
        
        # Verify all warmed
        for std in standards:
            assert redis_client.get(f"standard:{std}") is not None


class TestQuestionDifficultyCache:
    """Tests for difficulty-based question caching."""

    @pytest.fixture
    def redis_client(self, redis_url):
        import redis
        return redis.from_url(redis_url)

    def test_difficulty_level_buckets(self, redis_client):
        """RED-QDIFF-001: Verify questions grouped by difficulty buckets."""
        bucket_key = "questions:difficulty:3"  # Medium difficulty
        
        # Add questions to bucket
        questions = ["q1", "q2", "q3", "q4", "q5"]
        
        pipe = redis_client.pipeline()
        pipe.delete(bucket_key)
        for q in questions:
            pipe.sadd(bucket_key, q)
        pipe.expire(bucket_key, 1800)
        pipe.execute()
        
        # Verify bucket population
        members = redis_client.smembers(bucket_key)
        assert len(members) == 5

    def test_difficulty_filter_query(self, redis_client):
        """RED-QDIFF-002: Verify efficient difficulty filtering."""
        # Simulate query for questions at specific difficulty
        difficulty = 3
        filter_key = f"difficulty:{difficulty}"
        
        # Questions sorted by standard and difficulty score
        pipe = redis_client.pipeline()
        pipe.delete(filter_key)
        for i in range(10):
            pipe.zadd(filter_key, {f"q{i}": i * 0.1})
        pipe.expire(filter_key, 1800)
        pipe.execute()
        
        # Query questions in difficulty range
        results = redis_client.zrangebyscore(
            filter_key, 2.9, 3.1
        )
        assert len(results) > 0


class TestQuestionSelectionCache:
    """Tests for question selection caching."""

    @pytest.fixture
    def redis_client(self, redis_url):
        import redis
        return redis.from_url(redis_url)

    def test_cached_question_sequence(self, redis_client):
        """RED-QSEL-001: Verify question sequence can be cached."""
        sequence_key = "seq:assessment:123"
        
        # Cache question order for this assessment
        sequence = ["q001", "q002", "q003", "q004", "q005"]
        
        redis_client.setex(
            sequence_key,
            3600,
            ",".join(sequence)
        )
        
        # Retrieve sequence
        cached = redis_client.get(sequence_key)
        assert cached is not None
        assert len(cached.decode()) > 0

    def test_question_reuse_prevention(self, redis_client):
        """RED-QSEL-002: Verify answered questions are excluded from selection."""
        pool_key = "pool:active:123"
        answered_key = "answered:123"
        
        # Add questions to pool
        all_questions = ["q1", "q2", "q3", "q4", "q5", "q6"]
        pipe = redis_client.pipeline()
        pipe.delete(pool_key)
        for q in all_questions:
            pipe.sadd(pool_key, q)
        pipe.execute()
        
        # Mark some as answered
        answered = ["q1", "q2", "q3"]
        pipe = redis_client.pipeline()
        pipe.delete(answered_key)
        for q in answered:
            pipe.sadd(answered_key, q)
        pipe.execute()
        
        # Select un-answered questions
        remaining = redis_client.sdiff(pool_key, answered_key)
        assert len(remaining) == 3  # q4, q5, q6
