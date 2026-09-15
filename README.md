# SQL Agent

Ask your database questions in plain English and get back real results. Open the
page, say who you are, connect a Postgres or MySQL database, and type something
like "show me the top 10 customers by revenue last month" — it gets turned into
an actual SQL query and run against your data.

No accounts. Giving a name starts a session that lasts 24 hours; the databases
you connect and the questions you ask live in that session and disappear with it.

## Stack

**Backend** — FastAPI, Redis (the only datastore), LangChain + Groq for the agent.
Everything Python is under `backend/`.

**Frontend** — React + TypeScript, Vite, Tailwind, React Router, TanStack Query.

## Running it

### Docker (everything, including Redis)

```
cd backend
cp .env.example .env          # fill GROQ_API_KEY, SECRET_KEY, CREDENTIALS_KEY
docker compose up --build
```

The API serves on http://localhost:8000, docs at `/docs`.

### Backend locally, Redis in Docker

The usual loop while working on the backend: Redis in a container, the API on
your machine with reload. Needs Python 3.12+.

```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest                 # for the tests

cp .env.example .env               # fill in the three required values
docker compose up -d redis         # published on 127.0.0.1:6379
uvicorn app.main:app --reload
```

`.env` already points `REDIS_URL` at `localhost:6379`, so nothing else to set.
Stop Redis with `docker compose down` when you're done.

Run the tests with `pytest` from `backend/`.

### Frontend

```
cd frontend
npm install
npm run dev
```

Opens http://localhost:3000, which is one of the origins the API allows by
default. Point it elsewhere with `VITE_API_URL` in `frontend/.env`, and add that
origin to the API's `CORS_ORIGINS`.

## Configuration

Three values are required; everything else has a default. See
`backend/.env.example` for the full list.

| Variable | What it is |
|---|---|
| `GROQ_API_KEY` | Your Groq key. |
| `SECRET_KEY` | Signs the session cookie. Any long random string. |
| `CREDENTIALS_KEY` | Fernet key encrypting connection passwords before they go into Redis. |
| `REDIS_URL` | Defaults to `redis://localhost:6379/0`; compose sets it for you. |
| `GROQ_MODEL` | Defaults to `openai/gpt-oss-120b`. |
| `CORS_ORIGINS` | Exact browser origins, comma separated. |

Generate `CREDENTIALS_KEY` with:

```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

There is no `DATABASE_URL`. The app has no database of its own, and the databases
it queries are supplied at runtime by whoever is asking.

## Workflow

1. **Start a session.** `POST /api/session` with a name. The session id is built
   from that name and the timestamp, and comes back in a signed cookie. Everything
   after this is scoped to it.
2. **Connect a database.** `POST /api/connections` with host, port, user,
   password, database name. The credentials are verified by actually connecting
   before anything is stored, then the password is encrypted and kept in Redis.
3. **Ask a question.** `POST /api/connections/{id}/natural-query`.
4. **The agent works.** A tool-calling agent explores the schema and writes a
   query. Every statement it runs goes through the read-only guard first.
5. **You get results.** The rows come back with the SQL the agent settled on.
6. **Follow up.** The turn is saved, so "now only the ones in London" refines the
   previous question. Past conversations reload with their SQL and results intact.

## API

| Method | Path | |
|---|---|---|
| `POST` | `/api/session` | start a session from a name |
| `GET` | `/api/session` | who the caller is |
| `DELETE` | `/api/session` | end it now |
| `POST` | `/api/connections` | connect a database |
| `GET` | `/api/connections` | list them |
| `GET` | `/api/connections/{id}` | one, without its password |
| `DELETE` | `/api/connections/{id}` | forget it, and its conversations |
| `POST` | `/api/connections/{id}/natural-query` | ask a question |
| `GET` | `/api/connections/{id}/conversations` | history, most recent first |
| `GET` | `/api/connections/{id}/conversations/{conversation_id}` | one conversation, replayed |
| `GET` | `/health` | health check (pings Redis) |

Every endpoint but `POST /api/session` and `/health` needs the session cookie, so
browser clients must send `credentials: 'include'`.

## How it works

### Sessions

A name and a timestamp make the session id, with a random suffix so it is a
credential rather than a guess — a name and a rough arrival time are both things
an attacker can know. Starlette's `SessionMiddleware` signs that id into a cookie;
the id is all the cookie holds. Everything else is in Redis:

```
session:{sid}                          the session
session:{sid}:connections              connected databases, passwords encrypted
session:{sid}:conversations            conversations
session:{sid}:conv:{conv_id}:messages  the turns in one conversation
```

All of those keys carry the *same* absolute expiry, so a session and everything
hanging off it die together at the 24-hour mark rather than leaving orphans
behind. The deadline is fixed at creation, not extended on use: a session is a
visit, and a visit has a length. `backend/app/session/store.py` owns the key
names; nothing else builds a Redis key by hand.

### The URL is the state

What you are looking at lives in the query string, so a refresh, the back
button, or a reopened tab all land in the same place:

```
/workspace?session=venu-1789489589-HBlY&connection=cb37&conversation=9c2a
```

`useAppParams` (`frontend/src/hooks/useAppParams.ts`) is the only place those
params are read or written.

The session id is mirrored there for legibility and deep links, but it is **not**
what authenticates — that is the HttpOnly cookie. A URL sent to someone else
shows them the start screen, not your databases. If the URL and the cookie
disagree, the cookie wins and the URL is corrected.

### The agent

A tool-calling agent (`backend/app/query/agent`), not a fixed pipeline. The model
gets three tools — `list_tables`, `describe_table`, `run_query` — and loops until
it can answer, so it explores the schema instead of being handed a dump of it, and
self-corrects by reading the database's own error messages. The last query it ran
successfully is what you get back.

### The guard

Every statement the agent runs goes through `backend/app/query/guard` first. It
enforces read-only, single-database access: one SELECT (or CTE) only, no writes,
no reading or writing host files (`INTO OUTFILE`, `LOAD_FILE`, `pg_read_file`), no
system schemas (`information_schema`, `mysql`, `pg_catalog`), and no reaching
other databases. Quoted identifiers and keywords hiding inside string literals
don't fool it.

It's defence in depth, though — the real boundary is the account you connect with.

> Connect each database with a **read-only account scoped to that one database**.

### Observability

Logs and traces go through [Pydantic Logfire](https://pydantic.dev/docs/logfire),
configured in `backend/app/core/observability.py` and called from `main.py` before
anything else is imported. FastAPI, SQLAlchemy, Redis, and HTTPX are instrumented,
so requests, the SQL the agent runs, and the calls out to Groq all land as spans
on the same trace as the question that caused them. Without a token it prints to
the console and sends nothing.

## Layout

```
backend/
  Dockerfile  docker-compose.yml  .dockerignore
  pyproject.toml  requirements.txt  .env.example
  app/
    main.py
    core/         config, redis, crypto, observability, tracing
    session/      store (the Redis key layout), router, deps
    connections/  connect and manage databases
    query/        router, service, guard/, agent/, databases/
  tests/          the SQL guard
frontend/
  src/
    types/        the API's shapes, mirroring the Pydantic schemas
    lib/          fetch client, error type, cache keys, formatting
    api/          one module per resource, snake_case in, camelCase out
    hooks/        one concern each; useAppParams owns the URL
    components/   ui/ primitives, then one folder per feature
    pages/        landing, workspace
```

## Tests

```
cd backend && pytest
```

They cover the guard — the code standing between an LLM-written query and a
real database, where a regression is a security bug rather than a broken page.

The frontend is checked by the compiler: `cd frontend && npm run typecheck`.
