from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2b09bf794c95'
down_revision: Union[str, Sequence[str], None] = 'a074e3300adf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('points', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('ai_chat_count', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('ai_extract_count', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'ai_extract_count')
    op.drop_column('users', 'ai_chat_count')
    op.drop_column('users', 'points')
