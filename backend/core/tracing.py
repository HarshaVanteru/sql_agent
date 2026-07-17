"""LangSmith tracing status.

Tracing is switched on by environment variables the LangSmith SDK reads
directly (LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT -- see
backend/.env.example). This module doesn't configure tracing; it just reports
at startup whether it's on, so a missing key is obvious instead of silent.
"""
import os

import logfire

_TRUTHY = {"1", "true", "yes", "on"}


def tracing_enabled() -> bool:
    flag = os.getenv("LANGSMITH_TRACING") or os.getenv("LANGCHAIN_TRACING_V2", "")
    return flag.strip().lower() in _TRUTHY


def log_tracing_status() -> None:
    """Log whether LangSmith tracing is active. Called once at startup."""
    if not tracing_enabled():
        logfire.info("LangSmith tracing disabled")
        return

    project = os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT") or "default"
    has_key = bool(os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY"))
    if has_key:
        logfire.info("LangSmith tracing enabled (project: {project})", project=project)
    else:
        logfire.warning(
            "Tracing is on but no LangSmith API key is set; traces will not be sent"
        )
