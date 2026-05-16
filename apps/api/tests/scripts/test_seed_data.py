"""Tests for the JSON seed bank.

Pins the question-count target (≥ 132 per PRD Stage 1) and verifies that
every seed item is structurally valid (4 options, exactly one correct,
explanation present, difficulty in [1, 5]).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SEED = Path(__file__).resolve().parents[2] / "scripts" / "seed_data" / "grade4_questions.json"


@pytest.fixture(scope="module")
def seed_data() -> list[dict]:
    return json.loads(SEED.read_text())


@pytest.mark.unit
def test_seed_file_exists() -> None:
    assert SEED.exists(), f"Seed file missing: {SEED}"


@pytest.mark.unit
def test_seed_meets_prd_count(seed_data: list[dict]) -> None:
    """PRD Stage 1 § success criteria: ≥ 132 seed questions."""
    assert len(seed_data) >= 132, f"Only {len(seed_data)} seed items, need ≥ 132"


@pytest.mark.unit
def test_seed_covers_all_g3_g4_standards(seed_data: list[dict]) -> None:
    expected_g4 = {
        "4.OA.A.1", "4.OA.A.2", "4.OA.A.3", "4.OA.B.4", "4.OA.C.5",
        "4.NBT.A.1", "4.NBT.A.2", "4.NBT.A.3", "4.NBT.B.4", "4.NBT.B.5", "4.NBT.B.6",
        "4.NF.A.1", "4.NF.A.2", "4.NF.B.3", "4.NF.B.4", "4.NF.C.5", "4.NF.C.6", "4.NF.C.7",
        "4.GM.A.1", "4.GM.A.2", "4.GM.A.3", "4.GM.B.4", "4.GM.B.5",
        "4.GM.C.6", "4.GM.C.7", "4.GM.C.8", "4.GM.D.9",
        "4.DR.A.1", "4.DR.B.2", "4.DR.C.3",
    }
    expected_g3 = {
        "3.OA.A.4", "3.OA.C.7", "3.OA.D.8",
        "3.NBT.A.2", "3.NBT.A.3",
        "3.NF.A.1", "3.NF.A.3",
        "3.GM.C.7", "3.GM.D.8",
    }
    seen = {q["standard_code"] for q in seed_data}
    missing_g4 = expected_g4 - seen
    missing_g3 = expected_g3 - seen
    assert not missing_g4, f"Missing G4 standards: {sorted(missing_g4)}"
    assert not missing_g3, f"Missing G3 prerequisites: {sorted(missing_g3)}"


@pytest.mark.unit
def test_each_question_well_formed(seed_data: list[dict]) -> None:
    for i, q in enumerate(seed_data):
        assert q["question_type"] == "multiple_choice", f"Item {i}: only MC supported in seed"
        assert len(q["options"]) == 4, f"Item {i}: must have 4 options"
        labels = [o["key"] for o in q["options"]]
        assert labels == ["A", "B", "C", "D"], f"Item {i}: labels must be A-D in order"
        assert q["correct_answer"] in {"A", "B", "C", "D"}, f"Item {i}: bad correct_answer"
        assert isinstance(q["difficulty"], int) and 1 <= q["difficulty"] <= 5, (
            f"Item {i}: difficulty must be int in [1,5]"
        )
        assert q.get("explanation"), f"Item {i}: missing explanation"
        assert q["stem"].strip(), f"Item {i}: empty stem"


@pytest.mark.unit
def test_distractors_are_distinct(seed_data: list[dict]) -> None:
    for i, q in enumerate(seed_data):
        texts = [o["text"] for o in q["options"]]
        assert len(set(texts)) == 4, (
            f"Item {i}: duplicate option text in {q['standard_code']}: {texts}"
        )
