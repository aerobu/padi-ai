"""Add accuracy_percentage to practice_sessions

Revision ID: 006
Revises: 005
Create Date: 2026-05-16 00:00:00.000000

This migration adds the missing `accuracy_percentage` column on
`practice_sessions` that `complete_session` was already writing to (causing
500s). See execution-plan P1-T05 / bug C-6.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "practice_sessions",
        sa.Column("accuracy_percentage", sa.Float(), nullable=True),
    )
    op.add_column(
        "practice_sessions",
        sa.Column("question_count_answered", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("practice_sessions", "question_count_answered")
    op.drop_column("practice_sessions", "accuracy_percentage")
