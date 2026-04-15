"""
Redis client singleton for caching and session management.
"""

import json
from typing import Any, Dict, Optional, List
from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError
import logging

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis key prefixes
ASSESSMENT_STATE_KEY = "assessment:{id}:state"
ASSESSMENT_POOL_KEY = "assessment:{id}:pool"
ASSESSMENT_BKT_KEY = "assessment:{id}:bkt:{standard_code}"
CONSENT_ACTIVE_KEY = "consent:active:{user_id}"
ASSESSMENT_CURRENT_Q_KEY = "assessment:{id}:current_question"


class RedisClient:
    """Singleton Redis client with common operations."""

    def __init__(self):
        self._redis: Optional[Redis] = None

    async def connect(self) -> None:
        """Initialize Redis connection."""
        try:
            self._redis = from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,
            )
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection established")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

    async def get_redis(self) -> Redis:
        """Get Redis client, connecting if necessary."""
        if not self._redis:
            await self.connect()
        return self._redis

    # --- Assessment State Operations ---

    async def save_assessment_state(
        self,
        assessment_id: str,
        state: Dict[str, Any],
        ttl_seconds: int = 3600,  # 1 hour default
    ) -> None:
        """Save assessment state to Redis."""
        redis = await self.get_redis()
        key = ASSESSMENT_STATE_KEY.format(id=assessment_id)
        await redis.setex(
            key,
            ttl_seconds,
            json.dumps(state),
        )

    async def get_assessment_state(
        self, assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get assessment state from Redis."""
        redis = await self.get_redis()
        key = ASSESSMENT_STATE_KEY.format(id=assessment_id)
        value = await redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def delete_assessment_state(self, assessment_id: str) -> None:
        """Delete assessment state from Redis."""
        redis = await self.get_redis()
        key = ASSESSMENT_STATE_KEY.format(id=assessment_id)
        await redis.delete(key)

    # --- Question Pool Operations ---

    async def set_question_pool(
        self,
        assessment_id: str,
        questions: List[Dict[str, Any]],
        ttl_seconds: int = 3600,
    ) -> None:
        """Store question pool for an assessment."""
        redis = await self.get_redis()
        key = ASSESSMENT_POOL_KEY.format(id=assessment_id)
        await redis.setex(
            key,
            ttl_seconds,
            json.dumps(questions),
        )

    async def get_question_pool(
        self, assessment_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get question pool for an assessment."""
        redis = await self.get_redis()
        key = ASSESSMENT_POOL_KEY.format(id=assessment_id)
        value = await redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def remove_question_from_pool(
        self, assessment_id: str, question_id: str
    ) -> None:
        """Remove a question from the assessment pool."""
        redis = await self.get_redis()
        key = ASSESSMENT_POOL_KEY.format(id=assessment_id)
        await redis.srem(key, question_id)

    # --- BKT State Operations ---

    async def save_bkt_state(
        self,
        assessment_id: str,
        standard_code: str,
        bkt_state: Dict[str, float],
        ttl_seconds: int = 3600,
    ) -> None:
        """Save BKT state for a standard."""
        redis = await self.get_redis()
        key = ASSESSMENT_BKT_KEY.format(id=assessment_id, standard_code=standard_code)
        await redis.setex(
            key,
            ttl_seconds,
            json.dumps(bkt_state),
        )

    async def get_bkt_state(
        self, assessment_id: str, standard_code: str
    ) -> Optional[Dict[str, float]]:
        """Get BKT state for a standard."""
        redis = await self.get_redis()
        key = ASSESSMENT_BKT_KEY.format(id=assessment_id, standard_code=standard_code)
        value = await redis.get(key)
        if value:
            return json.loads(value)
        return None

    # --- Current Question Operations ---

    async def set_current_question(
        self,
        assessment_id: str,
        question_id: str,
        ttl_seconds: int = 60,  # Short TTL for current question
    ) -> None:
        """Set current question for assessment."""
        redis = await self.get_redis()
        key = ASSESSMENT_CURRENT_Q_KEY.format(id=assessment_id)
        await redis.setex(
            key,
            ttl_seconds,
            question_id,
        )

    async def get_current_question(
        self, assessment_id: str
    ) -> Optional[str]:
        """Get current question for assessment."""
        redis = await self.get_redis()
        key = ASSESSMENT_CURRENT_Q_KEY.format(id=assessment_id)
        return await redis.get(key)

    # --- Consent Operations ---

    async def set_active_consent(
        self, user_id: str, ttl_seconds: int = 31536000  # 1 year
    ) -> None:
        """Mark user as having active consent."""
        redis = await self.get_redis()
        key = CONSENT_ACTIVE_KEY.format(user_id=user_id)
        await redis.setex(key, ttl_seconds, "1")

    async def get_active_consent(self, user_id: str) -> bool:
        """Check if user has active consent."""
        redis = await self.get_redis()
        key = CONSENT_ACTIVE_KEY.format(user_id=user_id)
        value = await redis.get(key)
        return value is not None

    async def revoke_active_consent(self, user_id: str) -> None:
        """Revoke active consent."""
        redis = await self.get_redis()
        key = CONSENT_ACTIVE_KEY.format(user_id=user_id)
        await redis.delete(key)


# Singleton instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get singleton Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


async def init_redis() -> RedisClient:
    """Initialize and return Redis client."""
    client = get_redis_client()
    await client.connect()
    return client


async def shutdown_redis() -> None:
    """Shutdown Redis client."""
    if _redis_client:
        await _redis_client.close()
