"""add_notes_to_suspects

Revision ID: i1j2k3l4m5n6
Revises: f1a2b3c4d5e6
Create Date: 2025-11-26 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'i1j2k3l4m5n6'
down_revision = 'h1i2j3k4l5m6'
branch_labels = None
depends_on = None


def upgrade():
    # Check if suspects table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'suspects' not in tables:
        # Table doesn't exist yet, skip this migration
        return
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('suspects')]
    
    if 'notes' not in columns:
        # Add notes column to suspects table
        op.add_column('suspects', sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    # Check if suspects table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'suspects' not in tables:
        return
    
    # Check if column exists before dropping
    columns = [col['name'] for col in inspector.get_columns('suspects')]
    
    if 'notes' in columns:
        # Remove notes column from suspects table
        op.drop_column('suspects', 'notes')

