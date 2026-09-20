"""add_comment_model_and_update_activity_status

Revision ID: 5269351a4623
Revises: 71e8d90ad7c4
Create Date: 2026-03-16 20:16:44.923829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = '5269351a4623'
down_revision: Union[str, Sequence[str], None] = '71e8d90ad7c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    op.alter_column('activities', 'title',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    op.alter_column('activities', 'start_time',
               existing_type=mysql.DATETIME(),
               nullable=False)
    op.alter_column('activities', 'end_time',
               existing_type=mysql.DATETIME(),
               nullable=False)
    op.alter_column('activities', 'organizer_id',
               existing_type=mysql.INTEGER(),
               nullable=False)
    op.alter_column('activities', 'status',
               existing_type=mysql.VARCHAR(length=20),
               type_=sa.Enum('PENDING', 'RECRUITING', 'ONGOING', 'ENDED', name='activitystatus'),
               existing_nullable=True)
    op.drop_index(op.f('ix_activities_title'), table_name='activities')


def downgrade() -> None:
    op.create_index(op.f('ix_activities_title'), 'activities', ['title'], unique=False)
    op.alter_column('activities', 'status',
               existing_type=sa.Enum('PENDING', 'RECRUITING', 'ONGOING', 'ENDED', name='activitystatus'),
               type_=mysql.VARCHAR(length=20),
               existing_nullable=True)
    op.alter_column('activities', 'organizer_id',
               existing_type=mysql.INTEGER(),
               nullable=True)
    op.alter_column('activities', 'end_time',
               existing_type=mysql.DATETIME(),
               nullable=True)
    op.alter_column('activities', 'start_time',
               existing_type=mysql.DATETIME(),
               nullable=True)
    op.alter_column('activities', 'title',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
    op.drop_index(op.f('ix_comments_id'), table_name='comments')
    op.drop_table('comments')
