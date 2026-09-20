"""add preferences and feedback

Revision ID: cec056d263bb
Revises: 34da3182df77
Create Date: 2026-03-23 16:09:19.356663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = 'cec056d263bb'
down_revision: Union[str, Sequence[str], None] = '34da3182df77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('feedbacks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'RESOLVED', name='feedbackstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedbacks_id'), 'feedbacks', ['id'], unique=False)
    op.alter_column('activities', 'status',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.Enum('PENDING', 'REJECTED', 'RECRUITING', 'ONGOING', 'ENDED', name='activitystatus'),
               existing_nullable=True)
    op.add_column('users', sa.Column('preferences', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'preferences')
    op.alter_column('activities', 'status',
               existing_type=sa.Enum('PENDING', 'REJECTED', 'RECRUITING', 'ONGOING', 'ENDED', name='activitystatus'),
               type_=mysql.VARCHAR(length=50),
               existing_nullable=True)
    op.drop_index(op.f('ix_feedbacks_id'), table_name='feedbacks')
    op.drop_table('feedbacks')
