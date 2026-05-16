"""Add IRT b/a parameters to questions

Revision ID: 007
Revises: 006
Create Date: 2026-05-16 00:00:01.000000

Adds the IRT difficulty (b) and discrimination (a) parameters required by
PRD Stage 3 § 3.2. b is on the standard logit scale (≈ -3..+3, 0 = grade
level). a defaults to 1.0 (Rasch). Backfills b from the existing integer
difficulty (1..5) via the linear map (difficulty - 3) * 0.6, which puts
1 at -1.2 and 5 at +1.2.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("difficulty_b", sa.Float(), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("discrimination_a", sa.Float(), nullable=False, server_default="1.0"),
    )
    # Backfill difficulty_b from the integer difficulty (1..5).
    op.execute(
        "UPDATE questions SET difficulty_b = (difficulty - 3) * 0.6 "
        "WHERE difficulty_b IS NULL"
    )


def downgrade() -> None:
    op.drop_column("questions", "discrimination_a")
    op.drop_column("questions", "difficulty_b")
