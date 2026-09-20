"""add_group_id_to_document

Revision ID: 77db6e05493c
Revises: b9bbbd3350be
Create Date: 2026-03-16 19:04:00.501400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '77db6e05493c'
down_revision: Union[str, Sequence[str], None] = 'b9bbbd3350be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'documents', 'groups', ['group_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'documents', type_='foreignkey')
    op.drop_column('documents', 'group_id')
