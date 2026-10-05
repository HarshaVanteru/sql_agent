"""Reusable field validators.

min_length=1 lets "   " through, which is how a blank name, a blank host and a
blank question all reached the services that trusted them. These are the shared
fix, so a new field gets the same treatment by declaring it rather than by
remembering to.
"""
from typing import Annotated

from pydantic import AfterValidator, Field


def _non_blank(label: str):
    def check(value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError(f"{label} is required")
        return trimmed

    return check


def RequiredText(label: str, max_length: int) -> object:
    """A trimmed, non-blank string of at most `max_length` characters.

    Deliberately no min_length: a length constraint fires before any validator
    below it, so an empty string would be rejected with Pydantic's own "String
    should have at least 1 character" -- accurate, and useless to whoever is
    looking at the form. The blank check does the whole job and says "Name is
    required" for both empty and whitespace-only.
    """
    return Annotated[
        str,
        Field(max_length=max_length),
        AfterValidator(_non_blank(label)),
    ]


def _check_host(value: str) -> str:
    """A bare hostname or address -- not a URL, and not a connection string.

    People paste `https://db.example.com` or the whole DSN out of a password
    manager. Caught here, they get told what to remove; passed through, the
    driver fails with something about name resolution instead.
    """
    host = value.strip()
    if not host:
        raise ValueError("Host is required")
    if "://" in host:
        raise ValueError("Enter just the hostname, without http:// or a driver prefix")
    if "/" in host or "@" in host:
        raise ValueError("Enter just the hostname -- no username, password or database path")
    if any(character.isspace() for character in host):
        raise ValueError("Host cannot contain spaces")
    return host


Host = Annotated[str, Field(max_length=255), AfterValidator(_check_host)]
