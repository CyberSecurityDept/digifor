from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'custody_reports' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('custody_reports')]
    
    if 'investigator' in columns and 'created_by' in columns:
        op.drop_column('custody_reports', 'investigator')
    elif 'investigator' in columns and 'created_by' not in columns:
        op.alter_column('custody_reports', 'investigator', new_column_name='created_by')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'custody_reports' not in tables:
        return
    
    columns = [col['name'] for col in inspector.get_columns('custody_reports')]
    
    if 'created_by' in columns:
        op.alter_column('custody_reports', 'created_by', new_column_name='investigator')

