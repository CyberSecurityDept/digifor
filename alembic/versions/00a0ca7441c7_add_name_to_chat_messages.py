"""add_name_to_chat_messages

Revision ID: 00a0ca7441c7
Revises: 9bb43e1ad8d3
Create Date: 2025-11-18 14:03:56.527411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00a0ca7441c7'
down_revision: Union[str, None] = '9bb43e1ad8d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_messages', 'name')

