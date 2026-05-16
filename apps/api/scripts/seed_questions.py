"""Seed the question bank from JSON.

Reads `scripts/seed_data/grade4_questions.json` (135+ questions across 39
standards — covers all Grade-3 prerequisite + Grade-4 Oregon standards) and
inserts into `questions` + `question_options`. Idempotent: questions are
matched by (standard_id, stem) so re-runs don't create duplicates.

Usage:
    python -m scripts.seed_questions               # seed all
    python -m scripts.seed_questions --dry-run     # print what would happen
    python -m scripts.seed_questions --standard 4.NF.A.1   # one standard only

Replaces the previous 18-question hand-rolled file (fix P2-T01).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Make `src` importable when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings  # noqa: E402
from src.models.models import Question, QuestionOption, Standard  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SEED_FILE = Path(__file__).parent / "seed_data" / "grade4_questions.json"


def _load_seed(path: Path) -> list[dict]:
    """Load and lightly validate the seed file."""
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}, got {type(data).__name__}")
    for i, q in enumerate(data):
        required = {"standard_code", "stem", "options", "correct_answer", "difficulty"}
        missing = required - set(q)
        if missing:
            raise ValueError(f"Seed item {i} missing required keys: {sorted(missing)}")
        if len(q["options"]) != 4:
            raise ValueError(f"Seed item {i} must have exactly 4 options")
    return data


async def _get_standard_map(session: AsyncSession) -> dict[str, str]:
    """Return a map of standard_code → standard.id."""
    result = await session.execute(select(Standard))
    return {s.standard_code: s.id for s in result.scalars()}


async def _seed(dry_run: bool, only_standard: str | None) -> tuple[int, int]:
    """Seed questions. Returns (inserted, skipped)."""
    settings = get_settings()
    db_url = settings.DATABASE_URL.replace("psycopg2", "asyncpg")
    engine = create_async_engine(db_url)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    inserted = 0
    skipped = 0
    seed = _load_seed(SEED_FILE)
    if only_standard:
        seed = [q for q in seed if q["standard_code"] == only_standard]

    async with SessionLocal() as session:
        std_map = await _get_standard_map(session)

        for item in seed:
            std_id = std_map.get(item["standard_code"])
            if not std_id:
                logger.warning(
                    "Standard %s missing — run seed_oregon_standards first; skipping",
                    item["standard_code"],
                )
                skipped += 1
                continue

            # Idempotency: skip if a question with same (standard_id, stem) exists
            existing = await session.execute(
                select(Question).where(
                    Question.standard_id == std_id,
                    Question.question_text == item["stem"],
                )
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                continue

            if dry_run:
                logger.info("[dry-run] would insert %s — %s",
                            item["standard_code"], item["stem"][:60])
                inserted += 1
                continue

            q = Question(
                id=str(uuid4()),
                standard_id=std_id,
                question_text=item["stem"],
                question_type=item.get("question_type", "multiple_choice"),
                difficulty=int(item["difficulty"]),
                points=int(item.get("points", 1)),
                is_active=True,
                metadata_json={
                    "source": "seed",
                    "version": "1.1",
                },
            )
            session.add(q)
            await session.flush()

            correct_label = item["correct_answer"]
            for idx, opt in enumerate(item["options"]):
                session.add(
                    QuestionOption(
                        id=str(uuid4()),
                        question_id=q.id,
                        option_text=opt["text"],
                        is_correct=(opt["key"] == correct_label),
                        explanation=item.get("explanation") if opt["key"] == correct_label else None,
                        order=idx,
                    )
                )
            inserted += 1

        if not dry_run:
            await session.commit()

    await engine.dispose()
    return inserted, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the PADI.AI question bank.")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing.")
    parser.add_argument("--standard", help="Seed only this standard code, e.g. 4.NF.A.1")
    args = parser.parse_args()

    inserted, skipped = asyncio.run(_seed(args.dry_run, args.standard))
    logger.info("seed complete: inserted=%d skipped=%d (dry_run=%s)",
                inserted, skipped, args.dry_run)


if __name__ == "__main__":
    main()
