from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = '9bb43e1ad8d3'
down_revision: Union[str, None] = '70e296cc56e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if chat_messages table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'chat_messages' not in tables:
        # Table doesn't exist yet, skip this migration
        return
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    
    if 'account_name' not in columns:
        op.add_column('chat_messages', sa.Column('account_name', sa.String(), nullable=True))


def downgrade() -> None:
    # Check if chat_messages table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'chat_messages' not in tables:
        return
    
    # Check if column exists before dropping
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    
    if 'account_name' in columns:
        op.drop_column('chat_messages', 'account_name')

