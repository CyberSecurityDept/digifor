"""change_timezone_to_indonesia

Revision ID: h1i2j3k4l5m6
Revises: 8ffaa5edd56a
Create Date: 2025-11-25 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, None] = '8ffaa5edd56a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if tables exist before modifying
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Update evidence table
    if 'evidence' in tables:
        columns = {col['name']: col for col in inspector.get_columns('evidence')}
        
        # Update NULL values in updated_at to created_at value first
        if 'updated_at' in columns:
            op.execute("UPDATE evidence SET updated_at = created_at WHERE updated_at IS NULL")
        
        # Remove server_default from created_at and updated_at
        if 'created_at' in columns:
            op.alter_column('evidence', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
        
        if 'updated_at' in columns:
            op.alter_column('evidence', 'updated_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
    
    # Update custody_logs table
    if 'custody_logs' in tables:
        columns = {col['name']: col for col in inspector.get_columns('custody_logs')}
        
        if 'created_at' in columns:
            op.alter_column('custody_logs', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
    
    # Update custody_reports table
    if 'custody_reports' in tables:
        columns = {col['name']: col for col in inspector.get_columns('custody_reports')}
        
        # Update NULL values in updated_at to created_at value first
        if 'updated_at' in columns:
            op.execute("UPDATE custody_reports SET updated_at = created_at WHERE updated_at IS NULL")
        
        if 'created_at' in columns:
            op.alter_column('custody_reports', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
        
        if 'updated_at' in columns:
            op.alter_column('custody_reports', 'updated_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
    
    # Update suspects table
    if 'suspects' in tables:
        columns = {col['name']: col for col in inspector.get_columns('suspects')}
        
        # Update NULL values in updated_at to created_at value first
        if 'updated_at' in columns:
            op.execute("UPDATE suspects SET updated_at = created_at WHERE updated_at IS NULL")
        
        if 'created_at' in columns:
            op.alter_column('suspects', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
        
        if 'updated_at' in columns:
            op.alter_column('suspects', 'updated_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)


def downgrade() -> None:
    # Revert back to server_default=func.now()
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Revert evidence table
    if 'evidence' in tables:
        columns = {col['name']: col for col in inspector.get_columns('evidence')}
        
        if 'created_at' in columns:
            op.alter_column('evidence', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=sa.func.now(),
                          nullable=False)
        
        if 'updated_at' in columns:
            op.alter_column('evidence', 'updated_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
    
    # Revert custody_logs table
    if 'custody_logs' in tables:
        columns = {col['name']: col for col in inspector.get_columns('custody_logs')}
        
        if 'created_at' in columns:
            op.alter_column('custody_logs', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=sa.func.now(),
                          nullable=False)
    
    # Revert custody_reports table
    if 'custody_reports' in tables:
        columns = {col['name']: col for col in inspector.get_columns('custody_reports')}
        
        if 'created_at' in columns:
            op.alter_column('custody_reports', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=sa.func.now(),
                          nullable=False)
        
        if 'updated_at' in columns:
            op.alter_column('custody_reports', 'updated_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)
    
    # Revert suspects table
    if 'suspects' in tables:
        columns = {col['name']: col for col in inspector.get_columns('suspects')}
        
        if 'created_at' in columns:
            op.alter_column('suspects', 'created_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=sa.func.now(),
                          nullable=False)
        
        if 'updated_at' in columns:
            op.alter_column('suspects', 'updated_at',
                          existing_type=sa.DateTime(timezone=True),
                          server_default=None,
                          nullable=False)

