"""add notification model and group member status

Revision ID: 9834c9479f98
Revises: 2b09bf794c95
Create Date: 2026-03-26 20:35:50.143943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9834c9479f98'
down_revision: Union[str, Sequence[str], None] = '2b09bf794c95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('LIKE', 'COMMENT', 'ACTIVITY_APPROVAL', 'ACTIVITY_REJECTION', 'ACTIVITY_JOIN', 'GROUP_FILE_UPLOAD', 'GROUP_JOIN_REQUEST', 'GROUP_JOIN_APPROVAL', 'GROUP_JOIN_REJECTION', name='notificationtype'), nullable=False),
    sa.Column('content', sa.String(length=255), nullable=True),
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('target_type', sa.String(length=50), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.add_column('group_members', sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='groupmemberstatus'), nullable=True))
    op.add_column('group_members', sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))


def downgrade() -> None:
    op.drop_column('group_members', 'joined_at')
    op.drop_column('group_members', 'status')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
