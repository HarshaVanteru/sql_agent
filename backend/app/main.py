"""The application.

No accounts, no database of its own: a visitor gives a name, gets a session that
lasts 24 hours, connects their own database, and asks questions of it.
"""
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI, Response, status
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
from app.core.redis import check_connection, create_client, redacted_url  # noqa: E402
from app.core.tracing import log_tracing_status  # noqa: E402
from app.query.router import router as query_router  # noqa: E402
from app.session.router import router as session_router  # noqa: E402

log_tracing_status()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """One Redis client for the process, closed on the way out.

    The client is built lazily -- `create_client` opens no socket -- so the
    startup banner has to PING before it can honestly say anything about the
    connection. It used to announce "Connected to Redis" on the strength of
    having constructed the object, which meant a server with Redis down booted
    claiming to be healthy and then answered 503 to every request, with nothing
    in the log pointing at why.

    A failed check is reported, not raised: booting anyway is the deliberate
    design, so that a Redis which is briefly away does not stop the process
    coming up. Readiness is what reflects the outage -- see /health/ready.
    """
    app.state.redis = create_client()
    failure = await check_connection(app.state.redis)
    app.state.redis_ready = failure is None

    if failure is None:
        logfire.info("Connected to Redis at {url}", url=redacted_url())
    else:
        logfire.error(
            "Could not reach Redis at {url} ({error_type}). Starting anyway: requests "
            "that need the session store will answer 503 until it is back, and "
            "/health/ready will report not ready.",
            url=redacted_url(),
            error_type=failure,
        )

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
    """Liveness: is this process up and serving?

    Deliberately does not touch Redis. This is what the container healthcheck
    calls, and an unreachable Redis is not a reason to kill and restart the API
    -- restarting it does not bring Redis back, and a restart loop takes away
    the 503s that at least explain themselves. Whether the store is usable is a
    separate question, answered below.
    """
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
async def readiness(response: Response) -> dict[str, str]:
    """Readiness: can this process actually serve a request that needs Redis?

    503 when it cannot, so a load balancer takes this instance out of rotation
    rather than sending it traffic it will only refuse. Checked live on every
    call -- a cached answer from startup would still say "down" long after
    Redis came back.
    """
    failure = await check_connection(app.state.redis)
    app.state.redis_ready = failure is None
    if failure is not None:
        logfire.warning(
            "Readiness check could not reach Redis ({error_type})", error_type=failure
        )
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready", "redis": failure}
    return {"status": "ready", "redis": "ok"}


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
