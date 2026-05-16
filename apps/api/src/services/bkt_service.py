"""
Bayesian Knowledge Tracing (BKT) service.
Uses pyBKT library for knowledge state estimation.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Use pure Python BKT implementation to avoid pyBKT library compatibility issues
from src.services.bkt_impl import PyBKT
PYBKT_AVAILABLE = True

logger = logging.getLogger(__name__)


@dataclass
class BKTState:
    """Bayesian Knowledge Tracing state for a skill.

    NOTE: The dataclass uses `p_mastery/p_guess/p_slip/p_learning` while the
    `StudentSkillState` SQLAlchemy model stores
    `mastery_prob/guess_prob/slip_prob/learning_rate`. Always go through
    `bkt_state_from_row` / `apply_bkt_state_to_row` at the boundary; never
    set kwargs on the model directly.
    """

    p_mastery: float = 0.0   # P(L) — probability of mastery
    p_guess: float = 0.25    # P(G) — probability of guessing correctly
    p_slip: float = 0.2      # P(S) — probability of slipping
    p_learning: float = 0.5  # P(T) — probability of transitioning to mastered


def bkt_state_from_row(row: Any) -> BKTState:
    """Map a `StudentSkillState` ORM row to a `BKTState` dataclass.

    Centralized to keep field-name translation in one place (fix C-2/C-3).
    """
    return BKTState(
        p_mastery=row.mastery_prob if row.mastery_prob is not None else 0.0,
        p_guess=row.guess_prob if row.guess_prob is not None else 0.25,
        p_slip=row.slip_prob if row.slip_prob is not None else 0.20,
        p_learning=row.learning_rate if row.learning_rate is not None else 0.50,
    )


def apply_bkt_state_to_row(row: Any, state: BKTState) -> None:
    """Write a `BKTState` back to a `StudentSkillState` ORM row.

    Centralized to keep field-name translation in one place (fix C-2/C-3).
    """
    row.mastery_prob = state.p_mastery
    row.guess_prob = state.p_guess
    row.slip_prob = state.p_slip
    row.learning_rate = state.p_learning


class BKTService:
    """Stateless Bayesian Knowledge Tracing calculator.

    All methods are pure functions on inputs; no instance state is mutated.
    This is a deliberate redesign (fix C-4, 2026-05-16 review) — the previous
    implementation kept a process-wide `_bkt_instances` dict keyed only by
    `standard_code`, which caused concurrent students working on the same
    skill to corrupt each other's mastery state.
    """

    # Default BKT parameters (Corbett & Anderson 1994).
    DEFAULT_P_GUESS: float = 0.25
    DEFAULT_P_SLIP: float = 0.20
    DEFAULT_P_LEARNING: float = 0.50
    DEFAULT_P_MASTERY: float = 0.0

    def initialize_state(
        self,
        p_l0: Optional[float] = None,
        p_trans: Optional[float] = None,
        p_slip: Optional[float] = None,
        p_guess: Optional[float] = None,
    ) -> BKTState:
        """Return a fresh BKTState with the supplied (or default) parameters."""
        return BKTState(
            p_mastery=p_l0 if p_l0 is not None else self.DEFAULT_P_MASTERY,
            p_guess=p_guess if p_guess is not None else self.DEFAULT_P_GUESS,
            p_slip=p_slip if p_slip is not None else self.DEFAULT_P_SLIP,
            p_learning=p_trans if p_trans is not None else self.DEFAULT_P_LEARNING,
        )

    def update(self, prior: BKTState, response_correct: bool) -> BKTState:
        """Single-step BKT update — pure function.

        Returns a new BKTState; does not mutate `prior`.
        """
        bkt = PyBKT(
            p_l0=prior.p_mastery,
            p_trans=prior.p_learning,
            p_slip=prior.p_slip,
            p_guess=prior.p_guess,
        )
        bkt.forward_inference(is_correct=response_correct)
        return BKTState(
            p_mastery=bkt.p_l,
            p_guess=bkt.p_guess,
            p_slip=bkt.p_slip,
            p_learning=bkt.p_trans,
        )

    def update_state(
        self,
        standard_code: str,
        response_correct: bool,
        p_l0: Optional[float] = None,
        p_trans: Optional[float] = None,
        p_slip: Optional[float] = None,
        p_guess: Optional[float] = None,
    ) -> BKTState:
        """Back-compat wrapper. Prefer `update(prior, response_correct)`.

        Constructs a transient prior from kwargs and applies one BKT step.
        `standard_code` is accepted but ignored (no longer used for caching).
        """
        prior = self.initialize_state(
            p_l0=p_l0, p_trans=p_trans, p_slip=p_slip, p_guess=p_guess
        )
        return self.update(prior, response_correct)

    def predict_probability(self, state: BKTState) -> float:
        """P(correct | state) = P(L) * (1 - S) + (1 - P(L)) * G."""
        return (
            state.p_mastery * (1 - state.p_slip)
            + (1 - state.p_mastery) * state.p_guess
        )

    def batch_update(
        self,
        standard_code: str,
        responses: List[bool],
        p_l0: Optional[float] = None,
        p_trans: Optional[float] = None,
        p_slip: Optional[float] = None,
        p_guess: Optional[float] = None,
    ) -> BKTState:
        """Fold `update` over a response sequence and return the final state."""
        state = self.initialize_state(
            p_l0=p_l0, p_trans=p_trans, p_slip=p_slip, p_guess=p_guess
        )
        for is_correct in responses:
            state = self.update(state, is_correct)
        return state

    def get_state_dict(self, state: BKTState) -> Dict[str, float]:
        """Serialize a BKTState for Redis (uses BKTState field names)."""
        return {
            "p_mastery": state.p_mastery,
            "p_guess": state.p_guess,
            "p_slip": state.p_slip,
            "p_learning": state.p_learning,
        }

    def state_from_dict(self, data: Dict[str, float]) -> BKTState:
        """Deserialize a BKTState from a dict (Redis or API payload)."""
        return BKTState(
            p_mastery=data.get("p_mastery", 0.0),
            p_guess=data.get("p_guess", 0.25),
            p_slip=data.get("p_slip", 0.20),
            p_learning=data.get("p_learning", 0.50),
        )

    def classify_mastery(self, p_mastery: float) -> str:
        """Classify mastery level into 'low' | 'medium' | 'high'."""
        if p_mastery >= 0.80:
            return "high"
        if p_mastery >= 0.60:
            return "medium"
        return "low"


def get_bkt_service() -> BKTService:
    """Return a fresh `BKTService`. The service is stateless, so a new
    instance per call is cheap and prevents accidental shared-state bugs."""
    return BKTService()
