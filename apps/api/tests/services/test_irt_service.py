"""Unit tests for the 2PL IRT utilities."""

from __future__ import annotations

import math

import pytest

from src.services.irt_service import (
    DEFAULT_DISCRIMINATION,
    IRTItem,
    THETA_MAX,
    THETA_MIN,
    difficulty_band,
    difficulty_integer_to_b,
    information,
    probability_correct,
    select_max_information,
    update_theta,
)


@pytest.mark.unit
def test_probability_at_b_equals_one_half():
    """P(correct | θ = b) = 0.5 for any discrimination."""
    item = IRTItem(id="q1", b=0.5)
    assert probability_correct(0.5, item) == pytest.approx(0.5)


@pytest.mark.unit
def test_probability_monotonic_in_theta():
    item = IRTItem(id="q1", b=0.0)
    p_low = probability_correct(-1.0, item)
    p_mid = probability_correct(0.0, item)
    p_high = probability_correct(1.0, item)
    assert p_low < p_mid < p_high


@pytest.mark.unit
def test_information_max_at_theta_equals_b():
    item = IRTItem(id="q1", b=0.4, a=1.5)
    grid = [item.b + d for d in (-1.0, -0.5, 0.0, 0.5, 1.0)]
    info = [information(theta, item) for theta in grid]
    # Max value occurs at θ = b (index 2).
    assert info.index(max(info)) == 2


@pytest.mark.unit
def test_select_max_information_picks_closest_item():
    items = [
        IRTItem(id="a", b=-1.5),
        IRTItem(id="b", b=0.0),
        IRTItem(id="c", b=1.5),
    ]
    pick = select_max_information(0.1, items)
    assert pick is not None and pick.id == "b"


@pytest.mark.unit
def test_select_max_information_respects_exclusions():
    items = [IRTItem(id="a", b=0.0), IRTItem(id="b", b=0.1)]
    pick = select_max_information(0.0, items, exclude_ids={"a"})
    assert pick is not None and pick.id == "b"


@pytest.mark.unit
def test_update_theta_increases_on_correct_response():
    item = IRTItem(id="q1", b=0.0)
    new_theta = update_theta(theta=0.0, item=item, is_correct=True)
    assert new_theta > 0.0


@pytest.mark.unit
def test_update_theta_decreases_on_wrong_response():
    item = IRTItem(id="q1", b=0.0)
    new_theta = update_theta(theta=0.0, item=item, is_correct=False)
    assert new_theta < 0.0


@pytest.mark.unit
def test_update_theta_clamps_to_range():
    item = IRTItem(id="q1", b=0.0)
    # Far above grade level, correct response — should still clamp at 3.0
    theta = update_theta(theta=THETA_MAX - 0.01, item=item, is_correct=True)
    assert theta <= THETA_MAX
    theta = update_theta(theta=THETA_MIN + 0.01, item=item, is_correct=False)
    assert theta >= THETA_MIN


@pytest.mark.unit
def test_difficulty_band_for_each_mode():
    band = difficulty_band(0.0, "adaptive")
    assert band == (-0.3, 0.5)
    band = difficulty_band(1.0, "challenge")
    assert band == (1.3, 2.0)
    band = difficulty_band(-1.0, "scaffolded")
    assert band == (-2.0, -1.3)
    band = difficulty_band(0.0, "review")
    assert band == (-0.5, 0.0)


@pytest.mark.unit
def test_integer_to_b_mapping():
    assert difficulty_integer_to_b(1) == pytest.approx(-1.2)
    assert difficulty_integer_to_b(3) == pytest.approx(0.0)
    assert difficulty_integer_to_b(5) == pytest.approx(1.2)


@pytest.mark.unit
def test_default_discrimination():
    assert IRTItem(id="q", b=0.0).a == DEFAULT_DISCRIMINATION
