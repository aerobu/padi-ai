"""Promote generated_questions.content_embedding to pgvector

Revision ID: 008
Revises: 007
Create Date: 2026-05-16 00:00:02.000000

The model now mandates pgvector (P5-H01). This migration converts the
existing `content_embedding ARRAY(Float)` column to `Vector(384)` so the
column type matches the model. The cast is data-preserving for any rows
that already hold a 384-element vector; rows with NULL stay NULL.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure the extension exists in case earlier env had a bare Postgres
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # In-place type change via USING clause.
    op.execute(
        "ALTER TABLE generated_questions "
        "ALTER COLUMN content_embedding TYPE vector(384) USING content_embedding::vector"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE generated_questions "
        "ALTER COLUMN content_embedding TYPE float[] USING content_embedding::float[]"
    )
