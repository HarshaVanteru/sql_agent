import os

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.observability import configure_observability

# Before the routers are imported, not after: importing them creates the app's
# SQLAlchemy engine at module scope, and instrumentation only reaches engines
# created once it is in place.
configure_observability()

from backend.auth.router import router as auth_router  # noqa: E402
from backend.database.router import router as database_router  # noqa: E402
from backend.query.router import router as query_router  # noqa: E402
from backend.core.tracing import log_tracing_status  # noqa: E402

log_tracing_status()

app = FastAPI()

logfire.instrument_fastapi(app)

# Explicit origins, not "*". The CORS spec forbids pairing a wildcard with
# credentials, so Starlette resolves that combination by echoing back whichever
# Origin asked -- which is every origin, exactly what the wildcard looked like it
# was avoiding. The default is the Vite dev server; set CORS_ORIGINS (comma
# separated) for anywhere else.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(database_router)
app.include_router(query_router)
