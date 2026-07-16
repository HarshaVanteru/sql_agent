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

Every statement the agent tries goes through the read-only guard in `backend/query/guard.py` first: single statement, SELECT or CTE only, no data-modifying CTEs, and semicolons or keywords hiding inside string literals don't fool it.

Conversations are persisted (`conversations` / `messages`), so follow-ups work - ask "top 3 customers by spend", then "now only the ones in London", and the second question refines the first.

## Running it locally

Backend:
```
uv sync
uv run uvicorn backend.main:app --reload
```

You'll need a `backend/.env` with three things: `DATABASE_URL` (the app's own metadata store), `GROQ_API_KEY`, and `SECRET_KEY` (signs the JWTs). `ACCESS_TOKEN_EXPIRE_MINUTES` and `REFRESH_TOKEN_EXPIRE_DAYS` are optional and default to 15 and 30.

Run migrations with `alembic upgrade head` from `backend/`.

Frontend:
```
cd frontend
npm install
npm run dev
```

## Status

Auth (signup/login/logout, JWT + refresh) and database connection management are working. The agent supports Postgres and MySQL.

Known rough edges:
- **Connected-database passwords are stored in plaintext** in `database_credentials`, and `GET /api/databases/{id}` hands them back. Needs encrypting at rest.
- No test suite yet.
