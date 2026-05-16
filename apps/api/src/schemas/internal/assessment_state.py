"""Typed Redis-state schema for adaptive diagnostic assessments.

Centralizing this schema (instead of stuffing arbitrary dicts into Redis) is
the fix for bug C-1: previously `session_id` and `student_id` were never
persisted, so every downstream endpoint that looked them up returned None.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AssessmentRedisState(BaseModel):
    """Diagnostic assessment state held in Redis between requests."""

    assessment_id: str
    session_id: str
    student_id: str

    # Computerized Adaptive Testing state
    theta: float = 0.0
    questions_answered: int = 0
    covered_standards: dict[str, int] = Field(default_factory=dict)
    question_pool_size: int = 0

    # BKT state per skill (only mutated during diagnostic flow)
    bkt_states: dict[str, dict[str, float]] = Field(default_factory=dict)

    # Free-form metadata (kept minimal — should not balloon)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_redis_payload(self) -> dict[str, Any]:
        """JSON-serializable dict suitable for `RedisClient.save_assessment_state`."""
        return self.model_dump(mode="json")

    @classmethod
    def from_redis_payload(cls, data: dict[str, Any]) -> "AssessmentRedisState":
        """Parse a Redis payload back into a validated state object."""
        return cls.model_validate(data)
