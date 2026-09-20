"""add tags to group

Revision ID: d0a35ded15ed
Revises: 745753bb3a8e
Create Date: 2026-03-23 19:15:45.074130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd0a35ded15ed'
down_revision: Union[str, Sequence[str], None] = '745753bb3a8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('tags', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('groups', 'tags')
