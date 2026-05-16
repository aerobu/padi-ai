"""Unit tests for the stateless BKT service.

These tests pin behavior that was broken or unverified before the
2026-05-16 remediation: BKT determinism, statelessness across concurrent
calls, correct field-name translation between dataclass and ORM row.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from src.services.bkt_service import (
    BKTService,
    BKTState,
    apply_bkt_state_to_row,
    bkt_state_from_row,
)


@pytest.mark.unit
def test_update_is_pure_function():
    svc = BKTService()
    prior = svc.initialize_state()
    a = svc.update(prior, True)
    b = svc.update(prior, True)
    assert a == b
    # prior should be unchanged
    assert prior.p_mastery == svc.DEFAULT_P_MASTERY


@pytest.mark.unit
def test_correct_responses_increase_mastery():
    svc = BKTService()
    s = svc.initialize_state(p_l0=0.1)
    for _ in range(5):
        s = svc.update(s, True)
    assert s.p_mastery > 0.1


@pytest.mark.unit
def test_incorrect_responses_decrease_relative_to_correct():
    svc = BKTService()
    s0 = svc.initialize_state(p_l0=0.5)
    correct = svc.update(svc.update(s0, True), True)
    wrong = svc.update(svc.update(s0, False), False)
    assert correct.p_mastery > wrong.p_mastery


@pytest.mark.unit
def test_predict_probability_in_bounds():
    svc = BKTService()
    s = svc.initialize_state(p_l0=0.7)
    p = svc.predict_probability(s)
    assert 0.0 <= p <= 1.0


@pytest.mark.unit
def test_bkt_state_field_mapping_to_and_from_row():
    """Fix C-2/C-3: dataclass uses p_mastery, model uses mastery_prob.
    The helpers must translate both directions."""
    row = SimpleNamespace(
        mastery_prob=0.42,
        guess_prob=0.25,
        slip_prob=0.10,
        learning_rate=0.15,
    )
    state = bkt_state_from_row(row)
    assert state.p_mastery == pytest.approx(0.42)
    assert state.p_guess == pytest.approx(0.25)
    assert state.p_slip == pytest.approx(0.10)
    assert state.p_learning == pytest.approx(0.15)

    # Round-trip
    new_state = BKTState(p_mastery=0.9, p_guess=0.2, p_slip=0.05, p_learning=0.2)
    apply_bkt_state_to_row(row, new_state)
    assert row.mastery_prob == 0.9
    assert row.guess_prob == 0.2
    assert row.slip_prob == 0.05
    assert row.learning_rate == 0.2


@pytest.mark.unit
def test_bkt_state_from_row_handles_none():
    row = SimpleNamespace(
        mastery_prob=None,
        guess_prob=None,
        slip_prob=None,
        learning_rate=None,
    )
    state = bkt_state_from_row(row)
    assert state.p_mastery == 0.0
    assert state.p_guess == 0.25
    assert state.p_slip == 0.20
    assert state.p_learning == 0.50


# ---------------------------------------------------------------------------
# Concurrency: fix C-4 — no shared state across "students" using same skill.
# ---------------------------------------------------------------------------


@pytest.mark.concurrency
def test_50_parallel_updates_each_independent():
    """Two independent priors must not influence each other's results, even
    when invoked concurrently. Verifies the stateless redesign."""
    svc = BKTService()

    async def run_stream(seed_p: float, responses: list[bool]) -> float:
        state = svc.initialize_state(p_l0=seed_p)
        for r in responses:
            state = svc.update(state, r)
            # Yield control so streams interleave
            await asyncio.sleep(0)
        return state.p_mastery

    async def main() -> list[float]:
        streams = []
        # 50 streams: half "all correct", half "all wrong"
        for i in range(50):
            if i % 2 == 0:
                streams.append(run_stream(0.1, [True] * 5))
            else:
                streams.append(run_stream(0.1, [False] * 5))
        return await asyncio.gather(*streams)

    results = asyncio.run(main())
    even = [results[i] for i in range(0, 50, 2)]
    odd = [results[i] for i in range(1, 50, 2)]
    # Within each group: identical (same seed, same responses).
    assert all(r == even[0] for r in even)
    assert all(r == odd[0] for r in odd)
    # Between groups: clearly different.
    assert even[0] > odd[0]
