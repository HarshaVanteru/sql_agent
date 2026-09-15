"""The application.

No accounts, no database of its own: a visitor gives a name, gets a session that
lasts 24 hours, connects their own database, and asks questions of it.
"""
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.observability import configure_observability

# Before the routers are imported, not after: importing them reaches the engine
# cache used for the databases visitors connect, and instrumentation only
# reaches engines created once it is in place.
configure_observability()

from app.connections.router import router as connections_router  # noqa: E402
from app.core.redis import create_client  # noqa: E402
from app.core.tracing import log_tracing_status  # noqa: E402
from app.query.router import router as query_router  # noqa: E402
from app.session.router import router as session_router  # noqa: E402

log_tracing_status()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """One Redis client for the process, closed on the way out."""
    app.state.redis = create_client()
    logfire.info("Connected to Redis at {url}", url=settings.REDIS_URL)
    try:
        yield
    finally:
        await app.state.redis.aclose()


app = FastAPI(
    title="SQL Agent",
    description="Connect a database and ask it questions in plain English.",
    version="2.0.0",
    lifespan=lifespan,
)


register_error_handlers(app)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    """Health check. Redis is the only dependency, so it is the only thing to check."""
    try:
        await app.state.redis.ping()
    except Exception as e:
        # The type is the useful half and the only half that reliably survives
        # scrubbing: ConnectionError means it is down, AuthenticationError
        # means REDIS_URL is missing a password.
        logfire.warning(
            "Health check could not reach Redis ({error_type}): {error}",
            error_type=type(e).__name__,
            error=str(e),
        )
        return {"status": "degraded", "redis": type(e).__name__}
    return {"status": "ok", "redis": "ok"}


logfire.instrument_fastapi(app)

# Inside CORS, so a preflight is answered before any session work happens.
# The cookie carries only the session id, signed with SECRET_KEY.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_TTL_SECONDS,
    same_site=settings.SESSION_COOKIE_SAMESITE,
    https_only=settings.SESSION_COOKIE_SECURE,
)

# Explicit origins, not "*". The CORS spec forbids pairing a wildcard with
# credentials, so Starlette resolves that combination by echoing back whichever
# Origin asked -- which is every origin, exactly what the wildcard looked like it
# was avoiding. Set CORS_ORIGINS (comma separated) for anywhere else.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_router)
app.include_router(connections_router)
app.include_router(query_router)
