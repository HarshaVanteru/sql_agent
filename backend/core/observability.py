"""Logfire configuration and library instrumentation.

Configured exactly once, at application startup (backend/main.py). Everything
else in the codebase just calls `logfire.info(...)` and friends; no module needs
to import or set anything up first.

Console output keeps the INFO-and-above view the old stderr handler gave. The
DEBUG-and-above detail that used to go to a rotating logs/app.log now goes to the
Logfire backend instead, which only happens when LOGFIRE_TOKEN is set -- see the
README. Logfire has no file exporter, and writing one would defeat the point:
the backend is where traces, spans, and their attributes are meant to land.
"""
import os
import sys

import logfire

import backend.core.config  # noqa: F401  -- loads backend/.env before LOGFIRE_* is read

_FALSEY = {"0", "false", "no", "off"}


def _console_enabled() -> bool:
    """Whether to print to the console, honouring LOGFIRE_CONSOLE.

    Logfire reads that variable itself only when `console` is left unset, and we
    pass options, so it has to be read here or setting it would do nothing.
    """
    return os.getenv("LOGFIRE_CONSOLE", "true").strip().lower() not in _FALSEY


def _patch_otel_route_details() -> None:
    """Work around open-telemetry/opentelemetry-python-contrib#4732.

    FastAPI >= 0.137 puts `_IncludedRouter` objects in `app.routes`, and those have
    no `.path`. Naming a span, the instrumentor reads `.path` off whichever route
    matched: it guards that with a try/except when the match is full, but not when
    it is partial -- right path, wrong method. So a CORS preflight, or any
    wrong-method request, raised AttributeError and returned 500 instead of its
    405. Falling back to the request path is what the instrumentor's own full-match
    branch does. Once the fix is released this becomes a no-op and can be deleted.
    """
    from opentelemetry.instrumentation import fastapi as otel_fastapi

    original = otel_fastapi._get_route_details

    def _get_route_details(scope):
        try:
            return original(scope)
        except AttributeError:
            return scope.get("path")

    otel_fastapi._get_route_details = _get_route_details


def configure_observability() -> None:
    """Configure Logfire and instrument the libraries we use.

    Must be called once, before any SQLAlchemy engine is created: SQLAlchemy's
    instrumentor is a process-wide singleton that patches engine creation, so it
    only reaches engines built after it is installed, and a second call would be
    ignored with a warning.
    """
    _patch_otel_route_details()

    # A Windows console is cp1252, and model output routinely contains characters
    # it cannot encode (narrow no-break spaces, em dashes). Without this, logging
    # such a line raises UnicodeEncodeError instead of printing it. stderr rather
    # than Logfire's stdout default, to keep the old handler's stream.
    stream = sys.stderr
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(errors="backslashreplace")

    logfire.configure(
        service_name="sql-agent",
        # No token means nowhere to send telemetry. Without this the app would
        # refuse to start unconfigured; instead it runs with console output only,
        # which is what local development and the test suite want.
        send_to_logfire="if-token-present",
        console=(
            logfire.ConsoleOptions(min_log_level="info", output=stream)
            if _console_enabled()
            else False
        ),
    )

    # Patches engine creation, so this covers both the app's own metadata engine
    # and every cached engine built for a user's connected database
    # (backend/query/databases/engines.py), which are created on demand.
    logfire.instrument_sqlalchemy()
    # The Groq client the agent calls through, and LangSmith's trace uploader,
    # both go out over httpx.
    logfire.instrument_httpx()
