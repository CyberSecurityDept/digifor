from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '9bb43e1ad8d3'
down_revision: Union[str, None] = '70e296cc56e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('account_name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('chat_messages', 'account_name')

