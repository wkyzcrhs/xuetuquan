"""add status column to notifications table

Revision ID: bcdc735521da
Revises: 9834c9479f98
Create Date: 2026-03-26 20:58:04.971445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bcdc735521da'
down_revision: Union[str, Sequence[str], None] = '9834c9479f98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('notifications', sa.Column('status', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('notifications', 'status')
