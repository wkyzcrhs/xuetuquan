"""add_post_likes_table

Revision ID: eb2eb0f20827
Revises: c9559077d5b5
Create Date: 2026-04-06 19:12:01.723228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'eb2eb0f20827'
down_revision: Union[str, Sequence[str], None] = 'c9559077d5b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('post_likes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_likes_id'), 'post_likes', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_post_likes_id'), table_name='post_likes')
    op.drop_table('post_likes')
