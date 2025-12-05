"""change_suspect_name_to_text

Revision ID: 5b5749ce0944
Revises: 4f24cddaa08c
Create Date: 2025-12-05 20:16:43.904334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '5b5749ce0944'
down_revision: Union[str, None] = '4f24cddaa08c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'suspects' not in tables:
        return
    
    # Change name column from VARCHAR(200) to TEXT
    op.alter_column('suspects', 'name',
                    existing_type=sa.String(200),
                    type_=sa.Text(),
                    existing_nullable=False)
    
    # Also increase case_name column size from VARCHAR(200) to VARCHAR(500)
    op.alter_column('suspects', 'case_name',
                    existing_type=sa.String(200),
                    type_=sa.String(500),
                    existing_nullable=True)


def downgrade() -> None:
    # Check if suspects table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'suspects' not in tables:
        return
    
    # Revert name column from TEXT back to VARCHAR(200)
    op.alter_column('suspects', 'name',
                    existing_type=sa.Text(),
                    type_=sa.String(200),
                    existing_nullable=False)
    
    # Revert case_name column from VARCHAR(500) back to VARCHAR(200)
    op.alter_column('suspects', 'case_name',
                    existing_type=sa.String(500),
                    type_=sa.String(200),
                    existing_nullable=True)

