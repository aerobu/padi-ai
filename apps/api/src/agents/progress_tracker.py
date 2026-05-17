"""Progress Tracker — pure BKT update + mastery check.

PRD Stage 3 § 3.2 Progress Tracker. No LLM involvement. Uses the stateless
`BKTService` (fix C-4 from 2026-05-16 review) so concurrent students don't
contaminate each other's mastery state.
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.agents.state import BKTState, SessionState
from src.services.bkt_service import BKTService


# Mastery threshold per PRD Stage 3 § 3.2 (P(mastered) ≥ 0.95).
MASTERY_THRESHOLD = 0.95
MIN_CORRECT_STREAK = 5
MIN_ATTEMPTS = 5


class ProgressTrackerAgent:
    """Apply a BKT step for the current skill based on the last assessment."""

    def __init__(self) -> None:
        self.bkt = BKTService()

    async def __call__(self, state: SessionState) -> SessionState:
        assessment = state.get("last_assessment") or {}
        skill_id = state.get("current_skill_id", "unknown")
        is_correct = bool(assessment.get("is_correct"))

        bkt_states = dict(state.get("bkt_states") or {})
        existing = bkt_states.get(skill_id) or BKTState(
            skill_id=skill_id,
            p_mastered=0.0,
            p_transit=self.bkt.DEFAULT_P_LEARNING,
            p_slip=self.bkt.DEFAULT_P_SLIP,
            p_guess=self.bkt.DEFAULT_P_GUESS,
            correct_streak=0,
            attempt_count=0,
        )

        prior = self.bkt.initialize_state(
            p_l0=existing["p_mastered"],
            p_trans=existing["p_transit"],
            p_slip=existing["p_slip"],
            p_guess=existing["p_guess"],
        )
        updated = self.bkt.update(prior, is_correct)

        existing["p_mastered"] = updated.p_mastery
        existing["p_transit"] = updated.p_learning
        existing["p_slip"] = updated.p_slip
        existing["p_guess"] = updated.p_guess
        existing["correct_streak"] = (
            (existing.get("correct_streak", 0) + 1) if is_correct else 0
        )
        existing["attempt_count"] = existing.get("attempt_count", 0) + 1
        existing["last_updated"] = datetime.now(timezone.utc)

        bkt_states[skill_id] = existing
        state["bkt_states"] = bkt_states

        state["questions_answered"] = state.get("questions_answered", 0) + 1
        if is_correct:
            state["questions_correct"] = state.get("questions_correct", 0) + 1
            state["consecutive_correct"] = state.get("consecutive_correct", 0) + 1
            state["consecutive_wrong"] = 0
        else:
            state["consecutive_correct"] = 0
            state["consecutive_wrong"] = state.get("consecutive_wrong", 0) + 1

        # Mastery declared (PRD § 3.2) — caller decides what to do next.
        mastered = (
            existing["p_mastered"] >= MASTERY_THRESHOLD
            and existing["correct_streak"] >= MIN_CORRECT_STREAK
            and existing["attempt_count"] >= MIN_ATTEMPTS
        )
        if mastered:
            state["next_agent"] = "end"
            state["session_complete"] = True
        elif state.get("questions_answered", 0) >= 10:
            state["next_agent"] = "end"
            state["session_complete"] = True
        else:
            state["next_agent"] = "question_generator"

        return state
