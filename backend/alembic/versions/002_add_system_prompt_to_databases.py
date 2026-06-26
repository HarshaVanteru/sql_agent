"""Add system_prompt field to databases table.

Revision ID: 002_add_system_prompt
Revises: 644cb6809911
Create Date: 2026-06-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_system_prompt'
down_revision = '644cb6809911'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('databases', sa.Column('system_prompt', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('databases', 'system_prompt')
