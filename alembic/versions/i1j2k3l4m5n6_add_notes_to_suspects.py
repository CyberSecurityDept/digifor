"""add_notes_to_suspects

Revision ID: i1j2k3l4m5n6
Revises: f1a2b3c4d5e6
Create Date: 2025-11-26 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'i1j2k3l4m5n6'
down_revision = 'h1i2j3k4l5m6'
branch_labels = None
depends_on = None


def upgrade():
    # Add notes column to suspects table
    op.add_column('suspects', sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    # Remove notes column from suspects table
    op.drop_column('suspects', 'notes')

