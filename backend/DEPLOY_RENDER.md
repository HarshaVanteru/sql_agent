# Deploying this backend to Render

## What this package contains

- FastAPI SQL Agent backend
- Dockerfile for Render
- Alembic migrations run at startup
- `/health` endpoint for Render health checks
- Environment-variable based configuration
- `.env` excluded from the deployable package

## Important architecture note

The `DATABASE_URL` database is the application's own metadata database (users, saved database connections, conversations, etc.).

The databases users connect to are separate. A Render server cannot reach a user's MySQL at `localhost`. A local connector / tunnel is still required for that feature.

## Render setup

1. Push this `backend` directory to GitHub.
2. In Render, create a **Web Service** from the repository.
3. Choose **Docker** as the runtime.
4. Set the root directory to the directory containing this Dockerfile (for this package, `backend` if it is nested in the repository).
5. Set the health check path to `/health`.
6. Add the environment variables from `.env.example`.
7. Use a cloud-hosted MySQL database for `DATABASE_URL`.
8. Deploy.

The application starts with:

    alembic upgrade head
    uvicorn backend.main:app --host 0.0.0.0 --port $PORT
