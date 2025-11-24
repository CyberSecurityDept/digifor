"""remove_evidence_types_and_add_source

Revision ID: b1c2d3e4f5a6
Revises: a803b4f2ca97
Create Date: 2025-12-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a803b4f2ca97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Check if evidence table exists
    if 'evidence' not in tables:
        # Table doesn't exist yet, skip this migration
        return
    
    # Get columns from evidence table
    evidence_columns = [col['name'] for col in inspector.get_columns('evidence')]
    
    # Step 1: Drop foreign key constraint if evidence_type_id exists
    if 'evidence_type_id' in evidence_columns:
        # Get foreign key constraints
        fk_constraints = []
        for fk in inspector.get_foreign_keys('evidence'):
            if fk['constrained_columns'] == ['evidence_type_id']:
                fk_constraints.append(fk['name'])
        
        # Drop foreign key constraints
        for fk_name in fk_constraints:
            op.drop_constraint(fk_name, 'evidence', type_='foreignkey')
        
        # Step 2: Drop column evidence_type_id
        op.drop_column('evidence', 'evidence_type_id')
    
    # Step 3: Add source column if it doesn't exist
    if 'source' not in evidence_columns:
        op.add_column('evidence', sa.Column('source', sa.String(100), nullable=True))
    
    # Step 4: Add evidence_type column if it doesn't exist
    if 'evidence_type' not in evidence_columns:
        op.add_column('evidence', sa.Column('evidence_type', sa.String(100), nullable=True))
    
    # Step 5: Drop evidence_types table if it exists
    if 'evidence_types' in tables:
        op.drop_table('evidence_types')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Check if evidence table exists
    if 'evidence' not in tables:
        return
    
    # Step 1: Recreate evidence_types table
    if 'evidence_types' not in tables:
        op.create_table(
            'evidence_types',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(50), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        op.create_index('ix_evidence_types_id', 'evidence_types', ['id'], unique=False)
    
    # Get columns from evidence table
    evidence_columns = [col['name'] for col in inspector.get_columns('evidence')]
    
    # Step 2: Add evidence_type_id column if it doesn't exist
    if 'evidence_type_id' not in evidence_columns:
        op.add_column('evidence', sa.Column('evidence_type_id', sa.Integer(), nullable=True))
    
    # Step 3: Add foreign key constraint (recheck columns after adding)
    evidence_columns_after = [col['name'] for col in inspector.get_columns('evidence')]
    if 'evidence_type_id' in evidence_columns_after:
        # Check if foreign key already exists
        fk_exists = False
        for fk in inspector.get_foreign_keys('evidence'):
            if fk['constrained_columns'] == ['evidence_type_id']:
                fk_exists = True
                break
        
        if not fk_exists:
            op.create_foreign_key(
                'evidence_evidence_type_id_fkey',
                'evidence',
                'evidence_types',
                ['evidence_type_id'],
                ['id']
            )
    
    # Step 4: Drop evidence_type column if it exists
    if 'evidence_type' in evidence_columns:
        op.drop_column('evidence', 'evidence_type')
    
    # Step 5: Drop source column if it exists
    if 'source' in evidence_columns:
        op.drop_column('evidence', 'source')

