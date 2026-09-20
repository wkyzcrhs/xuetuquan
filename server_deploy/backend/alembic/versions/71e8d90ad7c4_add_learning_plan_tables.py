"""add_learning_plan_tables

Revision ID: 71e8d90ad7c4
Revises: 77db6e05493c
Create Date: 2026-03-16 19:21:27.509223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '71e8d90ad7c4'
down_revision: Union[str, Sequence[str], None] = '77db6e05493c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('learning_plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', 'ARCHIVED', name='planstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_plans_id'), 'learning_plans', ['id'], unique=False)
    op.create_table('daily_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('type', sa.Enum('READING', 'PRACTICE', 'QUIZ', name='tasktype'), nullable=True),
    sa.Column('is_completed', sa.Boolean(), nullable=True),
    sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['learning_plans.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_tasks_id'), 'daily_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_daily_tasks_scheduled_date'), 'daily_tasks', ['scheduled_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_daily_tasks_scheduled_date'), table_name='daily_tasks')
    op.drop_index(op.f('ix_daily_tasks_id'), table_name='daily_tasks')
    op.drop_table('daily_tasks')
    op.drop_index(op.f('ix_learning_plans_id'), table_name='learning_plans')
    op.drop_table('learning_plans')
