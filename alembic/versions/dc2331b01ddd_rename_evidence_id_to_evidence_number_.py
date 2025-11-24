"""rename_evidence_id_to_evidence_number_in_suspects

Revision ID: dc2331b01ddd
Revises: 
Create Date: 2025-11-16 22:10:50.267434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'dc2331b01ddd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if suspects table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'suspects' not in tables:
        # Table doesn't exist yet, skip this migration
        # The table will be created with the correct column name (evidence_number) by SQLAlchemy models
        return
    
    # Check if evidence_id column exists
    columns = [col['name'] for col in inspector.get_columns('suspects')]
    
    if 'evidence_id' in columns and 'evidence_number' not in columns:
        # Rename column evidence_id to evidence_number in suspects table
        op.alter_column('suspects', 'evidence_id',
                        new_column_name='evidence_number',
                        existing_type=sa.String(100),
                        existing_nullable=True)
    elif 'evidence_number' in columns:
        # Column already renamed, skip
        pass
    # If neither column exists, table will be created with correct column name by models


def downgrade() -> None:
    # Check if suspects table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'suspects' not in tables:
        return
    
    # Check if evidence_number column exists
    columns = [col['name'] for col in inspector.get_columns('suspects')]
    
    if 'evidence_number' in columns and 'evidence_id' not in columns:
        # Rename column evidence_number back to evidence_id in suspects table
        op.alter_column('suspects', 'evidence_number',
                        new_column_name='evidence_id',
                        existing_type=sa.String(100),
                        existing_nullable=True)

