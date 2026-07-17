# SQL Agent

Ask your database questions in plain English and get back real results. Connect a Postgres or MySQL database, type a question like "show me the top 10 customers by revenue last month", and it gets turned into an actual SQL query and run against your data.

Built this to stop context-switching into a DB client every time I wanted to check something during dev.

## Stack

**Backend** - FastAPI + SQLAlchemy (async), Alembic for migrations, LangChain + Groq for the agent, email/password auth with JWTs.

**Frontend** - React + Vite, Tailwind, React Router.

## Auth

Deliberately small: an account, a password, and a token. `users` + `sessions` is the whole schema.

Passwords are bcrypt-hashed. Login returns a short-lived HS256 access token (stateless, signed with `SECRET_KEY`) plus a refresh token; only the refresh token has server-side state, stored as a SHA-256 hash in `sessions` so a presented token can be looked up directly. Logout revokes the session, which is what makes refresh stop working - an access token stays valid until it expires, so keep `ACCESS_TOKEN_EXPIRE_MINUTES` short.

Endpoints are `POST /auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, and `GET /auth/me`.

## How the query pipeline works

It's a tool-calling agent (`backend/query/agent`), not a fixed pipeline. The model gets three tools - `list_tables`, `describe_table`, and `run_query` - and loops until it can answer, so it explores the schema instead of being handed a dump of it, and it self-corrects by reading the database's own error messages. The last query it runs successfully is what you get back.

Every statement - whether the agent wrote it or you typed it in SQL mode - goes through the guard in `backend/query/guard.py` first. It enforces read-only, single-database access: one SELECT (or CTE) only, no writes, no reading or writing host files (`INTO OUTFILE`, `LOAD_FILE`, `pg_read_file`), no system schemas (`information_schema`, `mysql`, `pg_catalog`), and no reaching other databases. Quoted identifiers and keywords hiding inside string literals don't fool it. It's defence in depth, though - the real boundary is a database user granted read-only access to only the one database, so connect databases with a least-privilege account.

Conversations are persisted (`conversations` / `messages`), so follow-ups work - ask "top 3 customers by spend", then "now only the ones in London", and the second question refines the first. Each turn saves the reply, the SQL, and a snapshot of the result, so a past conversation reloads exactly as you left it - browse them from the history panel in the sidebar (`GET /api/databases/{id}/conversations`).

## Running it locally

Backend:
```
uv sync
uv run uvicorn backend.main:app --reload
```

You'll need a `backend/.env` with four things: `DATABASE_URL` (the app's own metadata store), `GROQ_API_KEY`, `SECRET_KEY` (signs the JWTs), and `CREDENTIALS_KEY` (encrypts stored database passwords - generate one with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`). `ACCESS_TOKEN_EXPIRE_MINUTES` and `REFRESH_TOKEN_EXPIRE_DAYS` are optional and default to 15 and 30.

Run migrations with `alembic upgrade head` from `backend/`.

Frontend:
```
cd frontend
npm install
npm run dev
```

## Status

Auth (signup/login/logout, JWT + refresh) and database connection management are working. The agent supports Postgres and MySQL.

Connected-database credentials are encrypted at rest (`CREDENTIALS_KEY`) and never returned by the API.

Known rough edges:
- No per-user rate limiting or query timeout yet.
- No test suite yet.
