"""One error shape for the whole API.

Everything the app raises itself looks like:

    {"detail": {"code": "INVALID_CREDENTIALS", "message": "..."}}

FastAPI's own validation failures do not -- they arrive as a list of objects
describing each bad field. A client would need two parsers, so the handler below
converts them into the shape above, keeping the per-field detail under "fields"
so a form can put each message next to the input that caused it.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": {
                    "code": "VALIDATION_ERROR",
                    "message": first,
                    "fields": fields,
                }
            },
        )
