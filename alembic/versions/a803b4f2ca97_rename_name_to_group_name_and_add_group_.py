"""rename_name_to_group_name_and_add_group_id

Revision ID: a803b4f2ca97
Revises: 00a0ca7441c7
Create Date: 2025-11-18 14:42:30.276569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a803b4f2ca97'
down_revision: Union[str, None] = '00a0ca7441c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if chat_messages table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'chat_messages' not in tables:
        # Table doesn't exist yet, skip this migration
        return
    
    # Check columns
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    
    # Rename column 'name' to 'group_name' if 'name' exists and 'group_name' doesn't
    if 'name' in columns and 'group_name' not in columns:
        op.alter_column('chat_messages', 'name', new_column_name='group_name')
    
    # Add column 'group_id' if it doesn't exist
    if 'group_id' not in columns:
        op.add_column('chat_messages', sa.Column('group_id', sa.String(), nullable=True))


def downgrade() -> None:
    # Check if chat_messages table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'chat_messages' not in tables:
        return
    
    # Check columns
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    
    # Remove column 'group_id' if it exists
    if 'group_id' in columns:
        op.drop_column('chat_messages', 'group_id')
    
    # Rename 'group_name' back to 'name' if 'group_name' exists and 'name' doesn't
    if 'group_name' in columns and 'name' not in columns:
        op.alter_column('chat_messages', 'group_name', new_column_name='name')

