"""
Test Suite: Redis - Concurrent Access Tests

Purpose: Validate Redis handling of concurrent assessment sessions.
"""

import pytest
from datetime import datetime, timedelta, timezone


class TestConcurrentAssessmentSessions:
    """Tests for concurrent access prevention."""

    @pytest.fixture
    def redis_client(self, redis_url):
        import redis
        return redis.from_url(redis_url)

    def test_atomic_lock_acquisition(self, redis_client):
        """RED-CONC-001: Verify lock acquisition is atomic."""
        lock_key = "lock:assessment:123"
        
        # First acquisition
        result1 = redis_client.set(lock_key, "value", nx=True, ex=60)
        assert result1 is True  # Lock acquired
        
        # Second acquisition should fail
        result2 = redis_client.set(lock_key, "value", nx=True, ex=60)
        assert result2 is None  # Lock not available

    def test_lock_release(self, redis_client):
        """RED-CONC-002: Verify lock can be released."""
        lock_key = "lock:release:123"
        
        # Acquire lock
        redis_client.set(lock_key, "owner", nx=True, ex=60)
        assert redis_client.get(lock_key) is not None
        
        # Release lock
        redis_client.delete(lock_key)
        assert redis_client.get(lock_key) is None

    def test_lease_extension(self, redis_client):
        """RED-CONC-003: Verify lock can be extended (lease pattern)."""
        lock_key = "lock:lease:123"
        
        # Acquire initial lock
        redis_client.set(lock_key, "owner", nx=True, ex=60)
        
        # Extend lock
        redis_client.expire(lock_key, 120)
        
        # Verify extension
        ttl = redis_client.ttl(lock_key)
        assert ttl > 60  # Should be extended

    def test_lock_with_pid(self, redis_client):
        """RED-CONC-004: Verify lock includes process ID for debugging."""
        import os
        
        lock_key = "lock:with_pid:123"
        pid = os.getpid()
        
        # Lock with PID
        redis_client.setex(lock_key, 60, f"owner:{pid}")
        
        # Verify PID in lock value
        value = redis_client.get(lock_key)
        assert f"owner:{pid}" in value.decode()


class TestBatchCacheOperations:
    """Tests for batch Redis operations."""

    @pytest.fixture
    def redis_client(self, redis_url):
        import redis
        return redis.from_url(redis_url)

    def test_multi_operation_pipeline(self, redis_client):
        """RED-BATCH-001: Verify pipelined operations are atomic."""
        pipe = redis_client.pipeline()
        
        # Batch operations
        pipe.set("key1", "value1")
        pipe.set("key2", "value2")
        pipe.set("key3", "value3")
        
        # Execute atomically
        results = pipe.execute()
        
        assert results[0] is True
        assert results[1] is True
        assert results[2] is True

    def test_transaction_with_watch(self, redis_client):
        """RED-BATCH-002: Verify WATCH/MULTI for optimistic locking."""
        counter_key = "counter:assessment"
        
        # Set initial value
        redis_client.set(counter_key, 0)
        
        # Watch key
        redis_client.watch(counter_key)
        
        try:
            # Start transaction
            pipe = redis_client.pipeline(True)
            current = redis_client.get(counter_key)
            new_value = int(current) + 1 if current else 1
            
            pipe.set(counter_key, new_value)
            pipe.execute()
            
            # Verify increment
            result = redis_client.get(counter_key)
            assert int(result) == 1
        except redis.WatchError:
            # Transaction failed due to concurrent modification
            pass


class TestCacheInvalidation:
    """Tests for cache invalidation patterns."""

    @pytest.fixture
    def redis_client(self, redis_url):
        import redis
        return redis.from_url(redis_url)

    def test_key_pattern_deletion(self, redis_client):
        """RED-INVALID-001: Verify pattern-based key deletion."""
        # Create keys with pattern
        for i in range(5):
            redis_client.setex(f"assessment:123:q:{i}", 300, f"data_{i}")
        
        # Delete by pattern
        keys = redis_client.keys("assessment:123:*")
        if keys:
            redis_client.delete(*keys)
        
        # Verify deletion
        remaining = redis_client.keys("assessment:123:*")
        assert len(remaining) == 0

    def test_cache_bust_on_update(self, redis_client):
        """RED-INVALID-002: Verify cache busting on data update."""
        question_key = "question:456"
        
        # Set cached value
        redis_client.setex(question_key, 300, "old_value")
        
        # Invalidate on update
        redis_client.delete(question_key)
        assert redis_client.get(question_key) is None
        
        # Set new value
        redis_client.setex(question_key, 300, "new_value")
        
        # Verify update
        assert redis_client.get(question_key) is not None
