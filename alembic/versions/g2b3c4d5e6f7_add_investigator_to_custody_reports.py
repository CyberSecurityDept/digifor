"""add_investigator_to_custody_reports

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2025-12-31 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'g2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'custody_reports' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('custody_reports')]
    
    if 'investigator' not in columns:
        op.add_column('custody_reports', sa.Column('investigator', sa.String(100), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'custody_reports' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('custody_reports')]
    
    if 'investigator' in columns:
        op.drop_column('custody_reports', 'investigator')

