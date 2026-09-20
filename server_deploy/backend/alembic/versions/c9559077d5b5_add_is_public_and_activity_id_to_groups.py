"""add_is_public_and_activity_id_to_groups

Revision ID: c9559077d5b5
Revises: bcdc735521da
Create Date: 2026-04-06 18:56:28.765485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9559077d5b5'
down_revision: Union[str, Sequence[str], None] = 'bcdc735521da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('groups', sa.Column('is_public', sa.Integer(), nullable=True))
    op.add_column('groups', sa.Column('activity_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'groups', 'activities', ['activity_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'groups', type_='foreignkey')
    op.drop_column('groups', 'activity_id')
    op.drop_column('groups', 'is_public')
