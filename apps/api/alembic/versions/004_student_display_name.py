"""Drop students.first_name/last_name; add display_name + birth_year, avatar_id, is_active

Revision ID: 004
Revises: 003
Create Date: 2026-04-21
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns nullable first for backfill
    op.add_column("students", sa.Column("display_name", sa.String(), nullable=True))
    op.add_column("students", sa.Column("avatar_id", sa.String(), nullable=True, server_default="avatar_default"))
    op.add_column("students", sa.Column("birth_year", sa.Integer(), nullable=True))
    op.add_column("students", sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()))

    # Backfill display_name from first_name (best-effort, COPPA-minimal)
    # For existing rows, prefer first_name; fall back to "Student" if null.
    op.execute(
        "UPDATE students SET display_name = COALESCE(NULLIF(first_name, ''), 'Student') "
        "WHERE display_name IS NULL"
    )

    # Enforce NOT NULL on display_name / avatar_id / is_active
    op.alter_column("students", "display_name", nullable=False)
    op.alter_column("students", "avatar_id", nullable=False)
    op.alter_column("students", "is_active", nullable=False)

    # Drop plaintext PII columns
    op.drop_column("students", "first_name")
    op.drop_column("students", "last_name")
    op.drop_column("students", "date_of_birth")


def downgrade():
    # Best-effort reverse: re-add the legacy columns (data loss accepted)
    op.add_column("students", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("students", sa.Column("last_name", sa.String(), nullable=True))
    op.add_column("students", sa.Column("date_of_birth", sa.Date(), nullable=True))

    # Backfill first_name from display_name
    op.execute("UPDATE students SET first_name = display_name")
    op.execute("UPDATE students SET last_name = ''")

    op.alter_column("students", "first_name", nullable=False)
    op.alter_column("students", "last_name", nullable=False)

    op.drop_column("students", "is_active")
    op.drop_column("students", "birth_year")
    op.drop_column("students", "avatar_id")
    op.drop_column("students", "display_name")
