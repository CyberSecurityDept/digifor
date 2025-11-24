"""rename_investigator_to_created_by_in_custody_reports

Revision ID: f1a2b3c4d5e6
Revises: b1c2d3e4f5a6
Create Date: 2025-12-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Check if custody_reports table exists
    if 'custody_reports' not in tables:
        # Table doesn't exist yet, skip this migration
        return
    
    # Check if investigator column exists
    columns = [col['name'] for col in inspector.get_columns('custody_reports')]
    
    if 'investigator' in columns:
        # Rename investigator column to created_by
        op.alter_column('custody_reports', 'investigator', new_column_name='created_by')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Check if custody_reports table exists
    if 'custody_reports' not in tables:
        # Table doesn't exist yet, skip this migration
        return
    
    # Check if created_by column exists
    columns = [col['name'] for col in inspector.get_columns('custody_reports')]
    
    if 'created_by' in columns:
        # Rename created_by column back to investigator
        op.alter_column('custody_reports', 'created_by', new_column_name='investigator')

