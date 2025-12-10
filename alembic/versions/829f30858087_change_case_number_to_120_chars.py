"""change_case_number_to_120_chars

Revision ID: 829f30858087
Revises: 67bb93fbd300
Create Date: 2025-12-10 13:45:28.483251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '829f30858087'
down_revision: Union[str, None] = '67bb93fbd300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

