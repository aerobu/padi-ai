"""
Bayesian Knowledge Tracing (BKT) service.
Uses pyBKT library for knowledge state estimation.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

try:
    from pybkt.bkt import BKT as PyBKT
    PYBKT_AVAILABLE = True
except ImportError:
    PYBKT_AVAILABLE = False
    logging.warning(
        "pyBKT not installed. Installing from GitHub..."
    )
    # Fallback: Try to install
    import subprocess
    subprocess.run(
        ["pip", "install", "git+https://github.com/UC Berkeley-IRL/pyBKT"],
        capture_output=True,
    )
    from pybkt.bkt import BKT as PyBKT
    PYBKT_AVAILABLE = True

logger = logging.getLogger(__name__)


@dataclass
class BKTState:
    """Bayesian Knowledge Tracing state for a skill."""

    p_mastery: float = 0.0  # P(L) - Probability of mastery
    p_guess: float = 0.25   # P(G) - Probability of guessing correctly
    p_slip: float = 0.2     # P(S) - Probability of slipping
    p_learning: float = 0.5 # P(T) - Probability of transitioning to mastered state


class BKTService:
    """Service for Bayesian Knowledge Tracing operations."""

    # Default BKT parameters (standard values from Corbett & Anderson 1994)
    DEFAULT_P_GUESS = 0.25
    DEFAULT_P_SLIP = 0.20
    DEFAULT_P_LEARNING = 0.50
    DEFAULT_P_MASTERY = 0.0  # Start with no mastery assumed

    def __init__(self):
        """Initialize BKT service."""
        self._bkt_instances: Dict[str, PyBKT] = {}

    def get_or_create_bkt(
        self,
        standard_code: str,
        p_l0: Optional[float] = None,
        p_trans: Optional[float] = None,
        p_slip: Optional[float] = None,
        p_guess: Optional[float] = None,
    ) -> PyBKT:
        """Get or create a BKT instance for a standard."""
        if standard_code not in self._bkt_instances:
            self._bkt_instances[standard_code] = PyBKT(
                p_l0=p_l0 or self.DEFAULT_P_MASTERY,
                p_trans=p_trans or self.DEFAULT_P_LEARNING,
                p_slip=p_slip or self.DEFAULT_P_SLIP,
                p_guess=p_guess or self.DEFAULT_P_GUESS,
            )
        return self._bkt_instances[standard_code]

    def initialize_state(
        self,
        standard_code: str,
        p_l0: Optional[float] = None,
        p_trans: Optional[float] = None,
        p_slip: Optional[float] = None,
        p_guess: Optional[float] = None,
    ) -> BKTState:
        """Initialize BKT state for a standard."""
        return BKTState(
            p_mastery=p_l0 or self.DEFAULT_P_MASTERY,
            p_guess=p_guess or self.DEFAULT_P_GUESS,
            p_slip=p_slip or self.DEFAULT_P_SLIP,
            p_learning=p_trans or self.DEFAULT_P_LEARNING,
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
        """
        Update BKT state based on a student response.

        Args:
            standard_code: The standard/skill code
            response_correct: Whether the response was correct
            p_l0: Initial mastery probability (optional)
            p_trans: Transition probability (optional)
            p_slip: Slip probability (optional)
            p_guess: Guess probability (optional)

        Returns:
            Updated BKT state
        """
        bkt = self.get_or_create_bkt(
            standard_code=standard_code,
            p_l0=p_l0,
            p_trans=p_trans,
            p_slip=p_slip,
            p_guess=p_guess,
        )

        # Run BKT inference
        bkt.forward_inference(is_correct=response_correct)

        # Extract state
        state = bkt.get_node(standard_code).state

        return BKTState(
            p_mastery=state.p_l,
            p_guess=bkt.p_guess,
            p_slip=bkt.p_slip,
            p_learning=bkt.p_trans,
        )

    def predict_probability(
        self,
        standard_code: str,
        response_correct: bool,
        p_l0: Optional[float] = None,
        p_trans: Optional[float] = None,
        p_slip: Optional[float] = None,
        p_guess: Optional[float] = None,
    ) -> float:
        """
        Predict probability of correct response.

        P(C) = P(L) * (1 - S) + (1 - P(L)) * G

        Where:
        - P(L) = probability of mastery
        - S = slip probability
        - G = guess probability
        """
        state = self.update_state(
            standard_code=standard_code,
            response_correct=response_correct,
            p_l0=p_l0,
            p_trans=p_trans,
            p_slip=p_slip,
            p_guess=p_guess,
        )

        # P(correct) = P(mastery) * (1 - slip) + (1 - P(mastery)) * guess
        p_correct = (
            state.p_mastery * (1 - state.p_slip)
            + (1 - state.p_mastery) * state.p_guess
        )

        return p_correct

    def batch_update(
        self,
        standard_code: str,
        responses: List[bool],
        p_l0: Optional[float] = None,
        p_trans: Optional[float] = None,
        p_slip: Optional[float] = None,
        p_guess: Optional[float] = None,
    ) -> BKTState:
        """
        Update BKT state with a batch of responses.

        Args:
            standard_code: The standard/skill code
            responses: List of correct/incorrect responses (True/False)
            p_l0: Initial mastery probability (optional)
            p_trans: Transition probability (optional)
            p_slip: Slip probability (optional)
            p_guess: Guess probability (optional)

        Returns:
            Final BKT state after all responses
        """
        state = self.initialize_state(
            standard_code=standard_code,
            p_l0=p_l0,
            p_trans=p_trans,
            p_slip=p_slip,
            p_guess=p_guess,
        )

        for response in responses:
            state = self.update_state(
                standard_code=standard_code,
                response_correct=response,
                p_l0=state.p_mastery,  # Use updated mastery as new L0
                p_trans=p_trans or state.p_learning,
                p_slip=p_slip or state.p_slip,
                p_guess=p_guess or state.p_guess,
            )

        return state

    def get_state_dict(
        self, state: BKTState
    ) -> Dict[str, float]:
        """Convert BKTState to dictionary for Redis storage."""
        return {
            "p_mastery": state.p_mastery,
            "p_guess": state.p_guess,
            "p_slip": state.p_slip,
            "p_learning": state.p_learning,
        }

    def state_from_dict(
        self, data: Dict[str, float]
    ) -> BKTState:
        """Convert dictionary back to BKTState."""
        return BKTState(
            p_mastery=data.get("p_mastery", 0.0),
            p_guess=data.get("p_guess", 0.25),
            p_slip=data.get("p_slip", 0.20),
            p_learning=data.get("p_learning", 0.50),
        )

    def classify_mastery(
        self, p_mastery: float
    ) -> str:
        """
        Classify mastery level.

        Args:
            p_mastery: Probability of mastery (0.0 to 1.0)

        Returns:
            Classification string: 'low', 'medium', 'high'
        """
        if p_mastery >= 0.80:
            return "high"
        elif p_mastery >= 0.60:
            return "medium"
        else:
            return "low"

    def clear_instance(self, standard_code: str) -> None:
        """Clear BKT instance for a standard."""
        if standard_code in self._bkt_instances:
            del self._bkt_instances[standard_code]

    def clear_all(self) -> None:
        """Clear all BKT instances."""
        self._bkt_instances.clear()


# Singleton instance
_bkt_service: Optional[BKTService] = None


def get_bkt_service() -> BKTService:
    """Get singleton BKT service instance."""
    global _bkt_service
    if _bkt_service is None:
        _bkt_service = BKTService()
    return _bkt_service
