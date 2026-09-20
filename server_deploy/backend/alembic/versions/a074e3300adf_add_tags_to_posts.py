"""add tags to posts

Revision ID: a074e3300adf
Revises: d0a35ded15ed
Create Date: 2026-03-23 19:40:25.718687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a074e3300adf'
down_revision: Union[str, Sequence[str], None] = 'd0a35ded15ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('tags', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('posts', 'tags')
