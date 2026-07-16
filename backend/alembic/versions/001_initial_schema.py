"""Initial schema: accounts, sessions, connected databases, conversations.

Revision ID: 001_initial
Revises:
Create Date: 2026-07-16 17:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('refresh_token_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('ix_sessions_refresh_token_hash', 'sessions', ['refresh_token_hash'], unique=True)
    op.create_index('ix_sessions_expires_at', 'sessions', ['expires_at'])

    op.create_table(
        'databases',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('db_type', sa.String(50), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('name', 'user_id', name='uq_databases_name_user'),
    )
    op.create_index('ix_databases_user_id', 'databases', ['user_id'])

    op.create_table(
        'database_credentials',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('database_id', sa.String(36), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('password', sa.Text(), nullable=False),
        sa.Column('database_name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['database_id'], ['databases.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_database_credentials_database_id', 'database_credentials', ['database_id'], unique=True)

    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('database_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['database_id'], ['databases.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_database_id', 'conversations', ['database_id'])

    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('database_credentials')
    op.drop_table('databases')
    op.drop_table('sessions')
    op.drop_table('users')
