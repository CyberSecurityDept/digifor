"""rename_evidence_id_to_evidence_number_in_suspects

Revision ID: dc2331b01ddd
Revises: 
Create Date: 2025-11-16 22:10:50.267434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc2331b01ddd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column evidence_id to evidence_number in suspects table
    op.alter_column('suspects', 'evidence_id',
                    new_column_name='evidence_number',
                    existing_type=sa.String(100),
                    existing_nullable=True)


def downgrade() -> None:
    # Rename column evidence_number back to evidence_id in suspects table
    op.alter_column('suspects', 'evidence_number',
                    new_column_name='evidence_id',
                    existing_type=sa.String(100),
                    existing_nullable=True)

