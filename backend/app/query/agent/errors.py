"""Turning a model provider's failure into something worth showing.

The agent talks to Groq over HTTP, and an SDK exception's str() is the provider's
raw body:

    Error code: 401 - {'error': {'message': 'Invalid API Key', ...}}

Interpolating that into a user-facing message, which is what this used to do,
puts a JSON dump in a chat bubble. It also says the wrong thing: an invalid API
key is our configuration being wrong, not the question being wrong, so 400 was
never the right status either.

Each rule below decides three things -- whose fault it is, what the person
reading the screen can do about it, and what the log needs so whoever operates
this can fix it.
"""
from dataclasses import dataclass

from fastapi import status
from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from app.core.config import settings


@dataclass(frozen=True)
class ModelFailure:
    status_code: int
    code: str
    """What the person reading the screen is told."""
    message: str
    """What the log says, for whoever has to fix it. Never sent to the client."""
    operator_hint: str


def _config_problem(code: str, hint: str) -> ModelFailure:
    """Our setup is wrong. The visitor did nothing and can do nothing.

    502, not 500: the failure is in an upstream service we depend on. And the
    message admits it is our side rather than implying the question was bad.
    """
    return ModelFailure(
        status_code=status.HTTP_502_BAD_GATEWAY,
        code=code,
        message="The AI service isn't set up correctly on our side. This isn't your question.",
        operator_hint=hint,
    )


def classify(error: Exception) -> ModelFailure:
    """Map a provider exception onto an answer."""
    if isinstance(error, AuthenticationError):
        return _config_problem(
            "MODEL_AUTH_FAILED",
            "Groq rejected the API key. GROQ_API_KEY is missing, expired, or still "
            "the placeholder from .env.example. A real key starts with 'gsk_' and "
            "comes from console.groq.com/keys -- note that Grok (xAI) is a "
            "different product whose keys will never work here.",
        )

    if isinstance(error, PermissionDeniedError):
        return _config_problem(
            "MODEL_FORBIDDEN",
            f"Groq refused access to model {settings.GROQ_MODEL!r}. The key is valid "
            "but not entitled to it.",
        )

    if isinstance(error, NotFoundError):
        return _config_problem(
            "MODEL_NOT_FOUND",
            f"Groq has no model named {settings.GROQ_MODEL!r}. Check GROQ_MODEL "
            "against console.groq.com/docs/models -- model names are retired.",
        )

    if isinstance(error, RateLimitError):
        # The one case where waiting genuinely helps, so say so and mean it.
        return ModelFailure(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "MODEL_RATE_LIMITED",
            "The AI service is busy. Wait a moment and ask again.",
            "Groq rate limit reached -- per-minute tokens or requests on this key.",
        )

    if isinstance(error, (APITimeoutError, APIConnectionError)):
        return ModelFailure(
            status.HTTP_504_GATEWAY_TIMEOUT,
            "MODEL_UNAVAILABLE",
            "The AI service didn't respond in time. Try asking again.",
            f"Could not reach Groq (timeout is AGENT_LLM_TIMEOUT={settings.AGENT_LLM_TIMEOUT}s).",
        )

    if isinstance(error, InternalServerError):
        return ModelFailure(
            status.HTTP_502_BAD_GATEWAY,
            "MODEL_UNAVAILABLE",
            "The AI service had a problem. Try asking again.",
            "Groq returned a 5xx.",
        )

    if isinstance(error, BadRequestError):
        # Usually the conversation outgrew the model's context window, which the
        # person can act on by starting a new chat.
        return ModelFailure(
            status.HTTP_400_BAD_REQUEST,
            "MODEL_REJECTED_REQUEST",
            "The AI service couldn't process that. A shorter question, or a new "
            "conversation, usually helps.",
            "Groq rejected the request -- often context length. Lower "
            "MAX_HISTORY_MESSAGES or AGENT_ROW_SAMPLE if it persists.",
        )

    return ModelFailure(
        status.HTTP_502_BAD_GATEWAY,
        "MODEL_ERROR",
        "Something went wrong reaching the AI service. Try asking again.",
        "Unexpected failure from the agent.",
    )
