"""change_case_number_to_120_chars

Revision ID: 67bb93fbd300
Revises: c392790a338d
Create Date: 2025-12-10 13:45:25.525645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67bb93fbd300'
down_revision: Union[str, None] = 'c392790a338d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

