"""002_add_encrypted_email_fields

Revision ID: 1a4a929746ac
Revises: 001
Create Date: 2026-04-15 19:07:32.759039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a4a929746ac'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add encrypted email fields to users table for COPPA compliance."""
    # Add email_encrypted (BYTEA for AES encryption)
    op.add_column('users', sa.Column('email_encrypted', sa.LargeBinary(), nullable=True))

    # Add email_hash (SHA-256 hash for lookups without revealing email)
    op.add_column('users', sa.Column('email_hash', sa.String(64), nullable=True))

    # Create unique index on email_hash
    op.create_index('ix_users_email_hash', 'users', ['email_hash'], unique=True)

    # Note: Email data is now stored encrypted in email_encrypted
    # and hashed in email_hash for efficient lookups
    # The original email column is kept for backward compatibility during migration


def downgrade() -> None:
    """Remove encrypted email fields."""
    op.drop_index('ix_users_email_hash', table_name='users')
    op.drop_column('users', 'email_hash')
    op.drop_column('users', 'email_encrypted')
