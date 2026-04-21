"""
Pure Python Bayesian Knowledge Tracing (BKT) implementation.

This provides a lightweight BKT implementation that matches the expected API
from the original pyBKT library without external dependencies.

References:
- Corbett & Anderson (1994). Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge
- https://en.wikipedia.org/wiki/Knowledge_tracking#Bayesian_knowledge_tracing
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class BKTNode:
    """Node representing a skill's BKT state."""

    # Standard BKT parameters
    p_l0: float = 0.0      # Initial probability of mastery
    p_trans: float = 0.1   # Probability of learning (transition from non-mastery to mastery)
    p_slip: float = 0.2    # Probability of slipping (answering incorrectly despite mastery)
    p_guess: float = 0.25  # Probability of guessing correctly (answering correctly without mastery)

    # Current state
    p_l: float = 0.0       # Current probability of mastery (updated after each response)

    def copy(self) -> "BKTNode":
        """Create a copy of this node."""
        return BKTNode(
            p_l0=self.p_l0,
            p_trans=self.p_trans,
            p_slip=self.p_slip,
            p_guess=self.p_guess,
            p_l=self.p_l,
        )


class BKT:
    """
    Bayesian Knowledge Tracing model for a single skill.

    Implements the standard BKT algorithm with four parameters:
    - P(L0): Initial probability of mastery
    - P(T): Probability of learning (transition)
    - P(S): Slip probability
    - P(G): Guess probability
    """

    def __init__(
        self,
        p_l0: float = 0.0,
        p_trans: float = 0.1,
        p_slip: float = 0.2,
        p_guess: float = 0.25,
    ):
        """
        Initialize BKT model.

        Args:
            p_l0: Initial probability of mastery (0.0 to 1.0)
            p_trans: Probability of learning per opportunity (0.0 to 1.0)
            p_slip: Probability of slipping when mastered (0.0 to 1.0)
            p_guess: Probability of guessing correctly when not mastered (0.0 to 1.0)
        """
        # Validate inputs
        for name, value in [("p_l0", p_l0), ("p_trans", p_trans),
                           ("p_slip", p_slip), ("p_guess", p_guess)]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")

        self.p_l0 = p_l0
        self.p_trans = p_trans
        self.p_slip = p_slip
        self.p_guess = p_guess

        # Initialize state
        self.p_l = p_l0  # Current mastery probability

        # Track all states for get_node()
        self._states: list[BKTNode] = [BKTNode(
            p_l0=p_l0,
            p_trans=p_trans,
            p_slip=p_slip,
            p_guess=p_guess,
            p_l=p_l0,
        )]

        logger.debug(f"Initialized BKT: L0={p_l0}, T={p_trans}, S={p_slip}, G={p_guess}")

    def forward_inference(self, is_correct: bool) -> None:
        """
        Perform forward inference based on a student response.

        Updates the probability of mastery given whether the response was correct.

        P(L_t | C_{t-1}) = P(L_{t-1}) * P(T) + P(L_{t-1})
        P(L_t | ~C_{t-1}) = P(L_{t-1}) * (1 - P(T))

        Args:
            is_correct: True if student answered correctly, False otherwise
        """
        old_p_l = self.p_l

        if is_correct:
            # P(L|C) = P(L*(1-S) + (1-L)*G) / P(C)
            # P(C) = P(L)*(1-S) + (1-P(L))*G
            p_c = old_p_l * (1 - self.p_slip) + (1 - old_p_l) * self.p_guess

            if p_c > 0:
                # P(L|C) = P(C|L) * P(L) / P(C)
                # P(C|L) = 1 - S (probability of correct given mastery)
                self.p_l = (1 - self.p_slip) * old_p_l / p_c
            else:
                # This should never happen with valid parameters
                self.p_l = old_p_l
        else:
            # P(L|~C) = P(~C|L) * P(L) / P(~C)
            # P(~C) = P(L)*S + (1-P(L))*(1-G)
            p_not_c = old_p_l * self.p_slip + (1 - old_p_l) * (1 - self.p_guess)

            if p_not_c > 0:
                # P(~C|L) = S (probability of incorrect given mastery)
                self.p_l = self.p_slip * old_p_l / p_not_c
            else:
                # This should never happen with valid parameters
                self.p_l = 0.0

        # Apply learning transition
        # P(L_t) = P(L_{t-1}) * P(T) + P(L_{t-1})
        #        = P(L_{t-1}) * (P(T) + 1)
        # But this is wrong - we need to use law of total probability:
        # P(L_t) = P(L_t | L_{t-1}) * P(L_{t-1}) + P(L_t | ~L_{t-1}) * P(~L_{t-1})
        #        = P(L_{t-1}) * P(T) + P(L_{t-1})  # Wait, this is also wrong

        # Correct formula:
        # P(L_t = mastered) = P(L_t = mastered | L_{t-1} = mastered) * P(L_{t-1} = mastered)
        #                   + P(L_t = mastered | L_{t-1} = not mastered) * P(L_{t-1} = not mastered)
        #                   = 1 * P(L_{t-1}) + P(T) * (1 - P(L_{t-1}))
        #                   = P(L_{t-1}) + P(T) * (1 - P(L_{t-1}))
        #                   = P(L_{t-1}) * (1 - P(T)) + P(T)

        # After observing the response, we update:
        # P(L_t) = P(L_{t-1}|observation) + P(T) * (1 - P(L_{t-1}|observation))
        self.p_l = self.p_l + self.p_trans * (1 - self.p_l)

        # Clamp to valid range
        self.p_l = max(0.0, min(1.0, self.p_l))

        # Record state
        self._states.append(BKTNode(
            p_l0=self.p_l0,
            p_trans=self.p_trans,
            p_slip=self.p_slip,
            p_guess=self.p_guess,
            p_l=self.p_l,
        ))

        logger.debug(f"After response {'correct' if is_correct else 'incorrect'}: P(L)={self.p_l:.4f}")

    def get_node(self, standard_code: str = "default") -> BKTNode:
        """
        Get current BKT node state.

        Args:
            standard_code: Skill code (ignored in single-skill model)

        Returns:
            Current BKT node
        """
        if self._states:
            return self._states[-1]
        return BKTNode(
            p_l0=self.p_l0,
            p_trans=self.p_trans,
            p_slip=self.p_slip,
            p_guess=self.p_guess,
            p_l=self.p_l,
        )

    def reset(self) -> None:
        """Reset to initial state."""
        self.p_l = self.p_l0
        self._states = [BKTNode(
            p_l0=self.p_l0,
            p_trans=self.p_trans,
            p_slip=self.p_slip,
            p_guess=self.p_guess,
            p_l=self.p_l0,
        )]
        logger.debug(f"Reset BKT to initial state: P(L)={self.p_l0}")

    def predict_probability(self) -> float:
        """
        Predict probability of correct response.

        P(C) = P(L) * (1 - S) + (1 - P(L)) * G

        Returns:
            Probability of correct response
        """
        return self.p_l * (1 - self.p_slip) + (1 - self.p_l) * self.p_guess


class PyBKT(BKT):
    """
    Alias for BKT class to match original pyBKT API.

    This allows existing code to use `from pyBKT.bkt import BKT as PyBKT`
    while using our pure Python implementation.
    """
    pass
