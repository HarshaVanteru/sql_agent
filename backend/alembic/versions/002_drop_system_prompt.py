"""Drop databases.system_prompt.

The column was written at creation time but never read: the agent builds its own
prompt from backend/query/agent/prompts.py. The stored values were templates for
the retired pipeline, complete with a {schema} placeholder nothing filled in.

Revision ID: 002_drop_system_prompt
Revises: 001_initial
Create Date: 2026-07-16 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_drop_system_prompt'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('databases', 'system_prompt')


def downgrade() -> None:
    op.add_column('databases', sa.Column('system_prompt', sa.Text(), nullable=True))
