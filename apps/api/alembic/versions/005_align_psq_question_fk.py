"""Align practice_session_questions.question_id FK to generated_questions.id

Revision ID: 005
Revises: 004
Create Date: 2026-04-21
"""
from typing import Union
from alembic import op
from sqlalchemy import inspect

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels = None
depends_on = None


def upgrade():
    # Introspect the actual FK name since migration 003 created it anonymously.
    # Drop the FK pointing at questions.id, recreate pointing at generated_questions.id.
    conn = op.get_bind()
    insp = inspect(conn)
    fks = insp.get_foreign_keys("practice_session_questions")
    for fk in fks:
        if fk["constrained_columns"] == ["question_id"] and fk["referred_table"] == "questions":
            with op.batch_alter_table("practice_session_questions") as batch_op:
                batch_op.drop_constraint(fk["name"], type_="foreignkey")
                batch_op.create_foreign_key(
                    "fk_practice_session_questions_question_id_generated_questions",
                    "generated_questions",
                    ["question_id"],
                    ["id"],
                    ondelete="CASCADE",
                )
            break


def downgrade():
    conn = op.get_bind()
    insp = inspect(conn)
    fks = insp.get_foreign_keys("practice_session_questions")
    for fk in fks:
        if (
            fk["constrained_columns"] == ["question_id"]
            and fk["referred_table"] == "generated_questions"
        ):
            with op.batch_alter_table("practice_session_questions") as batch_op:
                batch_op.drop_constraint(fk["name"], type_="foreignkey")
                batch_op.create_foreign_key(
                    "fk_practice_session_questions_question_id_questions",
                    "questions",
                    ["question_id"],
                    ["id"],
                    ondelete="CASCADE",
                )
            break
