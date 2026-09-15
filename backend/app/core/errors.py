"""One error shape for the whole API, and a floor under every failure.

Everything the app raises itself already looks like:

    {"detail": {"code": "INVALID_CREDENTIALS", "message": "..."}}

The handlers here make that true of the failures it does *not* raise itself --
a validation error from FastAPI, a Redis that went away, a bug nobody planned
for. Without them those reach the client as a bare 500 with an empty body and
reach the log as a raw traceback, which tells whoever is looking at the screen
nothing at all.

None of this stops the process. An exception in a handler has never taken the
server down -- it fails that one request. What it used to do was fail it
*rudely*, and that is what changes here.
"""
import logfire
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from redis.exceptions import AuthenticationError as RedisAuthError
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError


def error_response(status_code: int, code: str, message: str, **extra) -> JSONResponse:
    """The one response shape, built in one place."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"code": code, "message": message, **extra}},
    )


def _field_path(location: tuple) -> str:
    """"body.credentials.host" -> "credentials.host", which is what a form knows."""
    parts = [str(part) for part in location if part != "body"]
    return ".".join(parts)


def _readable(message: str) -> str:
    """Pydantic prefixes its own messages; the prefix means nothing to a reader."""
    return message.removeprefix("Value error, ").removeprefix("Assertion failed, ")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for error in exc.errors():
            path = _field_path(error.get("loc", ()))
            # First message per field wins: one problem at a time is enough to
            # act on, and the first is the one nearest the cause.
            fields.setdefault(path or "body", _readable(error.get("msg", "Invalid value")))

        first = next(iter(fields.values()), "Check the values and try again.")
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", first, fields=fields
        )

    @app.exception_handler(RedisAuthError)
    async def storage_auth_failed(request: Request, exc: RedisAuthError) -> JSONResponse:
        """Redis is reachable but rejected us.

        Its own error text is not shown: it quotes the AUTH command, which
        reads like a leaked credential and gets redacted anyway. What actually
        helps is naming the setting to go and fix.
        """
        logfire.error(
            "Session store rejected our credentials on {method} {path} ({error_type}). "
            "Check REDIS_URL -- a password-protected Redis needs redis://:PASSWORD@host:port/0",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
        )
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "STORAGE_AUTH_FAILED",
            "Can't reach the session store right now. Try again in a moment.",
        )

    @app.exception_handler(RedisConnectionError)
    @app.exception_handler(RedisTimeoutError)
    async def storage_unreachable(request: Request, exc: Exception) -> JSONResponse:
        """Redis is down or unreachable, after the client already retried.

        503 rather than 500: nothing is wrong with the request, and trying it
        again shortly is exactly the right move -- which is what the message
        says, instead of handing over a stack trace.
        """
        logfire.error(
            "Session store unreachable on {method} {path} ({error_type}): {error}",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "STORAGE_UNAVAILABLE",
            "Can't reach the session store right now. Try again in a moment.",
        )

    @app.exception_handler(RedisError)
    async def storage_failed(request: Request, exc: RedisError) -> JSONResponse:
        """Any other Redis failure: a bad command, a full instance, a timeout
        mid-pipeline. Not retryable in the way a refused connection is."""
        logfire.exception(
            "Session store error on {method} {path} ({error_type}): {error}",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "STORAGE_ERROR",
            "The session store could not complete that. Try again in a moment.",
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        """The floor.

        Whatever went wrong, the client gets the same shape as every other
        error and nothing about our internals. The detail goes to the log,
        where it belongs -- an exception type and message in a response body
        is a map of the code for anyone who asks for it.
        """
        logfire.exception(
            "Unhandled {error_type} on {method} {path}: {error}",
            error_type=type(exc).__name__,
            method=request.method,
            path=request.url.path,
            error=str(exc),
        )
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "Something went wrong on our side. Try again.",
        )
