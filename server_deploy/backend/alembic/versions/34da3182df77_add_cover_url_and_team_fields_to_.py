"""add cover_url and team fields to activity

Revision ID: 34da3182df77
Revises: 5269351a4623
Create Date: 2026-03-22 19:49:53.857908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '34da3182df77'
down_revision: Union[str, Sequence[str], None] = '5269351a4623'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('cover_url', sa.String(length=255), nullable=True))
    op.add_column('activities', sa.Column('is_team', sa.Integer(), nullable=True))
    op.add_column('activities', sa.Column('team_limit', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'team_limit')
    op.drop_column('activities', 'is_team')
    op.drop_column('activities', 'cover_url')
