from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '8ffaa5edd56a'
down_revision: Union[str, None] = 'a946c11433e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at column to case_logs table (nullable first)
    op.add_column('case_logs', 
                  sa.Column('updated_at', 
                           sa.DateTime(), 
                           nullable=True))
    
    # Update existing rows to use created_at value
    op.execute("UPDATE case_logs SET updated_at = created_at")
    
    # Make column not nullable and remove server_default
    op.alter_column('case_logs', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=None)


def downgrade() -> None:
    op.drop_column('case_logs', 'updated_at')

