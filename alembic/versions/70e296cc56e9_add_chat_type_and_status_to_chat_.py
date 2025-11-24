"""add_chat_type_and_status_to_chat_messages

Revision ID: 70e296cc56e9
Revises: dc2331b01ddd
Create Date: 2025-11-18 10:37:21.792766

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '70e296cc56e9'
down_revision: Union[str, None] = 'dc2331b01ddd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if chat_messages table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'chat_messages' not in tables:
        # Table doesn't exist yet, skip this migration
        # The table will be created with the correct columns by SQLAlchemy models
        return
    
    # Check if columns already exist
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    
    if 'chat_type' not in columns:
        op.add_column('chat_messages', sa.Column('chat_type', sa.String(), nullable=True))
    if 'status' not in columns:
        op.add_column('chat_messages', sa.Column('status', sa.String(), nullable=True))


def downgrade() -> None:
    # Check if chat_messages table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'chat_messages' not in tables:
        return
    
    # Check if columns exist before dropping
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    
    if 'status' in columns:
        op.drop_column('chat_messages', 'status')
    if 'chat_type' in columns:
        op.drop_column('chat_messages', 'chat_type')

