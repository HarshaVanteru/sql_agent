# SQL Agent

Ask your database questions in plain English and get back real results. Connect a Postgres, MySQL, or MongoDB database, type a question like "show me the top 10 customers by revenue last month", and it gets turned into an actual SQL query (or Mongo query/aggregation) and run against your data.

Built this to stop context-switching into a DB client every time I wanted to check something during dev.

## Stack

**Backend** - FastAPI + SQLAlchemy (async), Alembic for migrations, LangChain/LangGraph + Groq for the NL -> query pipeline, Redis for rate limiting, JWT auth with 2FA (TOTP via pyotp).

**Frontend** - React + Vite, Tailwind, React Router.

## How the query pipeline works

Natural language in -> LLM generates the query -> a validation step checks it (blocks destructive stuff, checks it's actually valid for the target schema) -> executes -> formats the result back into something readable. SQL and NoSQL (Mongo) go through separate pipelines since the generation/validation logic is pretty different for each (`backend/query/sql` vs `backend/query/nosql`).

## Running it locally

Backend:
```
uv sync
uv run uvicorn backend.main:app --reload
```

You'll need a `backend/.env` with at minimum a `DATABASE_URL` (for the app's own auth/metadata store), `GROQ_API_KEY`, `SECRET_KEY`, `JWT_PRIVATE_KEY`/`JWT_PUBLIC_KEY`, and `REDIS_URL`. Check `backend/config` for the full list (SMTP settings for email, HIBP for breached-password checks, Google OAuth, etc. are all optional).

Run migrations with `alembic upgrade head` from `backend/`.

Frontend:
```
cd frontend
npm install
npm run dev
```

## Status

Auth (signup/signin/signout, JWT + refresh, 2FA) and database connection management are working. Query pipeline supports Postgres, MySQL, and MongoDB. Still rough around the edges in a few places - error messages from the LLM generation step could be friendlier, and I haven't added query history/saved queries yet.
