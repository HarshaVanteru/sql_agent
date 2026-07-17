# SQL Agent

Ask your database questions in plain English and get back real results. Connect a Postgres or MySQL database, type a question like "show me the top 10 customers by revenue last month", and it gets turned into an actual SQL query and run against your data.

Built this to stop context-switching into a DB client every time I wanted to check something during dev.

## Stack

**Backend** - FastAPI + SQLAlchemy (async), Alembic for migrations, LangChain + Groq for the agent, email/password auth with JWTs.

**Frontend** - React + Vite, Tailwind, React Router.

## Running the project

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 18+
- A MySQL or PostgreSQL server for the app's own metadata (accounts, connections, conversations). The databases you *query* are separate - you connect those from the UI.

### 1. Backend

Create `backend/.env`:

```
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/sql_agent
GROQ_API_KEY=your-groq-key
SECRET_KEY=any-long-random-string     # signs the JWTs
CREDENTIALS_KEY=your-fernet-key       # encrypts stored database passwords
```

Generate a `CREDENTIALS_KEY` with:

```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

`ACCESS_TOKEN_EXPIRE_MINUTES` and `REFRESH_TOKEN_EXPIRE_DAYS` are optional (default 15 and 30).

Install dependencies, run the migrations, and start the API - all from the repo root:

```
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --reload
```

The API serves on http://localhost:8000.

### 2. Frontend

```
cd frontend
npm install
npm run dev
```

Opens http://localhost:3000. To point it at a non-default backend, set `VITE_API_URL` in `frontend/.env` (see `.env.example`).

### 3. Use it

Sign up, then add a database connection (host, port, user, password, database name). Select it and start asking questions - or switch to SQL mode to write queries yourself.

> Connect each database with a **read-only account scoped to that one database**. The SQL guard blocks writes and cross-database access, but least-privilege credentials are the real safety net.

## Workflow

End to end, a question travels like this:

1. **Sign in.** Email/password login returns a short-lived access token (JWT) plus a refresh token. Every API call carries the access token.
2. **Connect a database.** Its credentials are encrypted at rest (Fernet) and never handed back by the API. Connections show up in the left sidebar.
3. **Ask a question.** Pick a database and type a question in plain English (or flip to SQL mode). The request hits `POST /api/databases/{id}/natural-query`.
4. **The agent works.** A tool-calling agent explores the schema and writes a query. Every statement it runs is checked by the read-only guard first.
5. **You get results.** The rows come back and render as a table, alongside the SQL the agent settled on.
6. **Follow up.** The turn is saved, so "now only the ones in London" refines the previous question. Past conversations are browsable from the sidebar and reload with their SQL and results intact.

The rest of this section is how each of those steps works underneath.

### The agent

It's a tool-calling agent (`backend/query/agent`), not a fixed pipeline. The model gets three tools - `list_tables`, `describe_table`, and `run_query` - and loops until it can answer, so it explores the schema instead of being handed a dump of it, and it self-corrects by reading the database's own error messages. The last query it runs successfully is what you get back.

### The guard

Every statement - whether the agent wrote it or you typed it in SQL mode - goes through the guard in `backend/query/guard` first. It enforces read-only, single-database access: one SELECT (or CTE) only, no writes, no reading or writing host files (`INTO OUTFILE`, `LOAD_FILE`, `pg_read_file`), no system schemas (`information_schema`, `mysql`, `pg_catalog`), and no reaching other databases. Quoted identifiers and keywords hiding inside string literals don't fool it. It's defence in depth, though - the real boundary is a database user granted read-only access to only the one database.

### Conversations

Conversations are persisted (`conversations` / `messages`), so follow-ups work - ask "top 3 customers by spend", then "now only the ones in London", and the second question refines the first. Each turn saves the reply, the SQL, and a snapshot of the result, so a past conversation reloads exactly as you left it - browse them from the history panel in the sidebar (`GET /api/databases/{id}/conversations`).

### Auth

Deliberately small: an account, a password, and a token. `users` + `sessions` is the whole schema.

Passwords are bcrypt-hashed. Login returns a short-lived HS256 access token (stateless, signed with `SECRET_KEY`) plus a refresh token; only the refresh token has server-side state, stored as a SHA-256 hash in `sessions` so a presented token can be looked up directly. Logout revokes the session, which is what makes refresh stop working - an access token stays valid until it expires, so keep `ACCESS_TOKEN_EXPIRE_MINUTES` short.

Endpoints: `POST /auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, and `GET /auth/me`.

### Observability

Logs and traces go through [Pydantic Logfire](https://pydantic.dev/docs/logfire), configured once in `backend/core/observability.py` and called from `main.py` before anything else is imported. FastAPI, SQLAlchemy, and HTTPX are instrumented, so requests, the SQL the agent runs, and the calls out to Groq all show up as spans on the same trace as the question that caused them.

Nothing is required to run the app: without a token it prints to the console and sends nothing (`send_to_logfire="if-token-present"`). To send traces to Logfire, run `uv run logfire auth` and set in `backend/.env`:

```
LOGFIRE_TOKEN=your-write-token
LOGFIRE_ENVIRONMENT=dev       # optional, filters projects in the UI
LOGFIRE_CONSOLE=false         # optional, silences the local console output
```

The console shows INFO and above, as the old stderr handler did. The DEBUG-level detail that used to go to a rotating `logs/app.log` now goes to Logfire instead - the file log is gone, along with `LOG_DIR`.

## Project layout

```
backend/
  core/       config + observability (Logfire)
  auth/       models, router, schemas, service, deps, security
  database/   models, router, schemas, service, crypto (connection management)
  query/      models, router, schemas, service, guard, agent/, databases/
  alembic/    migrations
  main.py
frontend/
  src/
    api/        central client (base URL + authed fetch)
    components/ sidebars, chat, modal
    context/    auth
    pages/      landing, login, signup, app
```

Each of `models`, `router`, `schemas`, `service`, and `guard` is a package folder (`__init__.py` holds the code).

## Status

Auth (signup/login/logout, JWT + refresh) and database connection management are working. The agent supports Postgres and MySQL.

Connected-database credentials are encrypted at rest (`CREDENTIALS_KEY`) and never returned by the API.

Known rough edges:
- No per-user rate limiting or query timeout yet.
- No test suite yet.
