"""Store the answer, SQL, and result on each assistant message.

Messages used to keep a single `content` column that held either the SQL the
agent ran or a plain-text reply, so a saved conversation could not be shown back
to the user faithfully. This splits them:
  - content   -> the reply as the user saw it (plain text)
  - sql_query -> the SQL the agent ran, for follow-up context and display
  - result    -> a snapshot of columns/rows/row_count returned to the user

Existing assistant rows held SQL in `content`; that SQL is moved into sql_query.
Old rows have no stored result and keep a null `result`.

Revision ID: 004_message_result_snapshot
Revises: 003_encrypt_credentials
Create Date: 2026-07-16 19:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_message_result_snapshot'
down_revision = '003_encrypt_credentials'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('sql_query', sa.Text(), nullable=True))
    op.add_column('messages', sa.Column('result', sa.JSON(), nullable=True))

    # Move SQL that was stored in `content` into the new column. A read-only
    # query starts with SELECT or WITH (see backend/query/guard.py); anything
    # else was a plain reply and stays in `content`.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, content FROM messages WHERE role = 'assistant'")
    ).fetchall()
    moved = 0
    for row_id, content in rows:
        if content and content.strip().lower().startswith(('select', 'with')):
            conn.execute(
                sa.text("UPDATE messages SET sql_query = :q, content = '' WHERE id = :i"),
                {'q': content, 'i': row_id},
            )
            moved += 1
    if moved:
        print(f'  moved {moved} assistant SQL message(s) into sql_query')


def downgrade() -> None:
    # Put the SQL back into content for the rows we emptied, so dropping the
    # column does not lose it.
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE messages SET content = sql_query "
        "WHERE role = 'assistant' AND sql_query IS NOT NULL "
        "AND (content = '' OR content IS NULL)"
    ))
    op.drop_column('messages', 'result')
    op.drop_column('messages', 'sql_query')
