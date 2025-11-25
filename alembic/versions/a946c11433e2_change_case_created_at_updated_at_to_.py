from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a946c11433e2'
down_revision: Union[str, None] = 'g2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('cases', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    nullable=False)
    op.alter_column('cases', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    nullable=False)
    
    op.alter_column('case_logs', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    nullable=False)


def downgrade() -> None:
    op.alter_column('cases', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False)
    op.alter_column('cases', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False)
    
    op.alter_column('case_logs', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False)

