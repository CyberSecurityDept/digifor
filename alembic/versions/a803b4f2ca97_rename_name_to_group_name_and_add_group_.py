"""rename_name_to_group_name_and_add_group_id

Revision ID: a803b4f2ca97
Revises: 00a0ca7441c7
Create Date: 2025-11-18 14:42:30.276569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a803b4f2ca97'
down_revision: Union[str, None] = '00a0ca7441c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column 'name' to 'group_name'
    op.alter_column('chat_messages', 'name', new_column_name='group_name')
    
    # Add column 'group_id'
    op.add_column('chat_messages', sa.Column('group_id', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove column 'group_id'
    op.drop_column('chat_messages', 'group_id')
    
    # Rename column 'group_name' back to 'name'
    op.alter_column('chat_messages', 'group_name', new_column_name='name')

