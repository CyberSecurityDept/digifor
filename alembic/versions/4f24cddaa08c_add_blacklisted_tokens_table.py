"""add_blacklisted_tokens_table

Revision ID: 4f24cddaa08c
Revises: i1j2k3l4m5n6
Create Date: 2025-12-03 16:51:11.130366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '4f24cddaa08c'
down_revision: Union[str, None] = 'i1j2k3l4m5n6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'blacklisted_tokens' in tables:
        # Table already exists, skip this migration
        return
    
    # Create blacklisted_tokens table
    op.create_table(
        'blacklisted_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_blacklisted_token_hash')
    )
    op.create_index(op.f('ix_blacklisted_tokens_id'), 'blacklisted_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_blacklisted_tokens_token_hash'), 'blacklisted_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    # Check if table exists before dropping
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'blacklisted_tokens' not in tables:
        return
    
    op.drop_index(op.f('ix_blacklisted_tokens_token_hash'), table_name='blacklisted_tokens')
    op.drop_index(op.f('ix_blacklisted_tokens_id'), table_name='blacklisted_tokens')
    op.drop_table('blacklisted_tokens')

