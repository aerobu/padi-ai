"""Item Response Theory utilities for the adaptive question selector.

Two-parameter logistic (2PL) model:

    P(correct | θ, a, b) = 1 / (1 + exp(-a (θ − b)))

where:
    θ = student ability
    a = item discrimination (default 1.0 → Rasch)
    b = item difficulty (logit scale; 0 ≈ grade level)

Information function:
    I(θ, a, b) = a^2 · P(θ) · (1 − P(θ))

Maximum-information question selection picks the item with the highest
I(θ, a, b) — i.e. the one whose difficulty is closest to the student's
current ability estimate (PRD Stage 3 § 3.2).

θ updates (MLE step):
We use a single-step Newton-Raphson update after each response. Clamp θ to
[-3, 3] to keep selection sane when the student is far from grade level.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


THETA_MIN = -3.0
THETA_MAX = 3.0
DEFAULT_DISCRIMINATION = 1.0


@dataclass(frozen=True)
class IRTItem:
    """Minimal IRT item shape (id + parameters)."""

    id: str
    b: float
    a: float = DEFAULT_DISCRIMINATION


def probability_correct(theta: float, item: IRTItem) -> float:
    """2PL P(correct | θ, item)."""
    z = item.a * (theta - item.b)
    # Clamp z to avoid math.exp overflow on extreme inputs.
    z = max(-50.0, min(50.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def information(theta: float, item: IRTItem) -> float:
    """Fisher information I(θ, item) for a 2PL item."""
    p = probability_correct(theta, item)
    return (item.a ** 2) * p * (1.0 - p)


def select_max_information(
    theta: float,
    items: Iterable[IRTItem],
    exclude_ids: Iterable[str] = (),
) -> IRTItem | None:
    """Return the item whose information at θ is maximum."""
    excluded = set(exclude_ids)
    best: IRTItem | None = None
    best_score = -math.inf
    for item in items:
        if item.id in excluded:
            continue
        score = information(theta, item)
        if score > best_score:
            best = item
            best_score = score
    return best


def update_theta(
    theta: float,
    item: IRTItem,
    is_correct: bool,
    step_size: float = 1.0,
) -> float:
    """Single Newton-Raphson update on θ given one response.

    θ_{t+1} = θ_t + (step_size · (u − P)) / I

    where u is 1 for correct / 0 for wrong, P = P(correct | θ, item),
    and I is Fisher information. Falls back to a small additive update when
    I is near zero (avoids division blow-ups).
    """
    p = probability_correct(theta, item)
    i = information(theta, item)
    u = 1.0 if is_correct else 0.0
    if i < 1e-6:
        # Fallback: tiny additive nudge in the right direction.
        delta = step_size * (0.05 if is_correct else -0.05)
    else:
        delta = step_size * (u - p) / i
    new_theta = theta + delta
    return max(THETA_MIN, min(THETA_MAX, new_theta))


def difficulty_band(theta: float, mode: str = "adaptive") -> tuple[float, float]:
    """Return (b_min, b_max) for question-pool filtering (PRD § 3.2)."""
    if mode == "challenge":
        return (theta + 0.3, theta + 1.0)
    if mode == "scaffolded":
        return (theta - 1.0, theta - 0.3)
    if mode == "review":
        return (theta - 0.5, theta)
    # adaptive (default) → Zone of Proximal Development band
    return (theta - 0.3, theta + 0.5)


def difficulty_integer_to_b(difficulty: int) -> float:
    """Map the legacy integer difficulty (1..5) to the IRT b-parameter.

    Same mapping as migration 007's backfill: (d − 3) * 0.6.
    """
    return (difficulty - 3) * 0.6
