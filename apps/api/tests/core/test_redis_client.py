"""Tests for Redis client infrastructure."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestRedisClientInitialization:
    """Test RedisClient initialization."""

    def test_redis_client_creation(self):
        """RedisClient can be created."""
        from src.core.redis_client import RedisClient

        with patch("redis.asyncio.Redis") as mock_redis:
            mock_redis.return_value = AsyncMock()
            client = RedisClient("redis://localhost:6379")
            assert client is not None
            assert client._redis is not None


class TestAssessmentStateCache:
    """Test assessment state caching."""

    @pytest.mark.asyncio
    async def test_save_assessment_state(self):
        """save_assessment_state stores state in Redis."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock, MagicMock

        mock_redis = AsyncMock()
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        state = {
            "theta": 0.5,
            "covered_standards": {"4.NBT.A.1": 3},
            "questions_answered": 10,
        }

        await client.save_assessment_state("assessment-123", state)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "assessment:assessment-123:state" in str(call_args[0])

    @pytest.mark.asyncio
    async def test_get_assessment_state(self):
        """get_assessment_state retrieves state from Redis."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value='{"theta": 0.5, "count": 10}')
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        result = await client.get_assessment_state("assessment-123")

        assert result is not None
        assert result["theta"] == 0.5
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_assessment_state_none(self):
        """get_assessment_state returns None for missing state."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        result = await client.get_assessment_state("missing-assessment")

        assert result is None


class TestBKTStateCache:
    """Test BKT state caching."""

    @pytest.mark.asyncio
    async def test_save_bkt_state(self):
        """save_bkt_state stores BKT state in Redis."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        bkt_state = {"p_mastery": 0.85, "p_guess": 0.25}

        await client.save_bkt_state("assessment-123", "4.NBT.A.1", bkt_state)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "assessment:assessment-123:bkt" in str(call_args[0][0])

    @pytest.mark.asyncio
    async def test_get_bkt_state(self):
        """get_bkt_state retrieves BKT state from Redis."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value='{"p_mastery": 0.85, "p_guess": 0.25}'
        )
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        result = await client.get_bkt_state("assessment-123", "4.NBT.A.1")

        assert result is not None
        assert result["p_mastery"] == 0.85
        assert result["p_guess"] == 0.25


class TestQuestionPoolCache:
    """Test question pool caching."""

    @pytest.mark.asyncio
    async def test_set_question_pool(self):
        """set_question_pool stores question pool in Redis."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        question_pool = [{"id": "q1", "difficulty": 3}]

        await client.set_question_pool("assessment-123", question_pool)

        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_question_pool(self):
        """get_question_pool retrieves question pool from Redis."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value='[{"id": "q1", "difficulty": 3}]'
        )
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        result = await client.get_question_pool("assessment-123")

        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "q1"


class TestActiveConsentCache:
    """Test active consent caching."""

    @pytest.mark.asyncio
    async def test_set_active_consent(self):
        """set_active_consent marks consent as active."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        await client.set_active_consent("user-123")

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "consent:user-123:active" in str(call_args[0][0])
        assert call_args[1]["ex"] == 31536000  # 1 year in seconds

    @pytest.mark.asyncio
    async def test_get_active_consent(self):
        """get_active_consent returns True if consent exists."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="active")
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        result = await client.get_active_consent("user-123")

        assert result is True
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_consent_false(self):
        """get_active_consent returns False if no consent."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        result = await client.get_active_consent("user-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_active_consent(self):
        """revoke_active_consent removes consent cache."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        await client.revoke_active_consent("user-123")

        mock_redis.delete.assert_called_once()
        call_args = mock_redis.delete.call_args
        assert "consent:user-123:active" in str(call_args[0][0])


class TestDeleteOperations:
    """Test Redis delete operations."""

    @pytest.mark.asyncio
    async def test_delete_assessment_state(self):
        """delete_assessment_state removes assessment state."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        await client.delete_assessment_state("assessment-123")

        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self):
        """delete removes arbitrary key."""
        from src.core.redis_client import RedisClient
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        client = RedisClient("redis://localhost:6379")
        client._redis = mock_redis

        await client.delete("assessment-123:some_key")

        mock_redis.delete.assert_called_once()


class TestRedisClientSingleton:
    """Test Redis client singleton pattern."""

    def test_get_redis_client_singleton(self):
        """get_redis_client returns same instance."""
        from src.core.redis_client import get_redis_client

        with patch("src.core.redis_client.RedisClient") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            client1 = get_redis_client()
            client2 = get_redis_client()

            assert client1 is client2
            mock_class.assert_called_once()
