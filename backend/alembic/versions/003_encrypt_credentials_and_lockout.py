"""Encrypt stored credentials and add login lockout.

Two changes that both harden auth:
  - database_credentials.password held plaintext. Existing rows are encrypted in
    place with CREDENTIALS_KEY; the column type is unchanged (ciphertext is text).
  - users gains failed_login_attempts / locked_until so repeated bad passwords
    lock an account instead of being free to retry.

Revision ID: 003_encrypt_credentials
Revises: 002_drop_system_prompt
Create Date: 2026-07-16 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

from backend.database.crypto import encrypt


# revision identifiers, used by Alembic.
revision = '003_encrypt_credentials'
down_revision = '002_drop_system_prompt'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))

    # Encrypt whatever plaintext is already stored. Running this twice would
    # double-encrypt, so it must not be re-applied without a downgrade first.
    conn = op.get_bind()
    rows = conn.execute(sa.text('SELECT id, password FROM database_credentials')).fetchall()
    for row_id, password in rows:
        conn.execute(
            sa.text('UPDATE database_credentials SET password = :p WHERE id = :i'),
            {'p': encrypt(password), 'i': row_id},
        )
    if rows:
        print(f'  encrypted {len(rows)} stored credential(s)')


def downgrade() -> None:
    # Deliberately not decrypting: reversing this would write plaintext passwords
    # back to disk. Re-enter the connections instead if you must roll back.
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
