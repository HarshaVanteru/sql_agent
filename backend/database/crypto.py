"""Encryption for stored connected-database credentials.

These passwords are reversibly encrypted rather than hashed: the agent has to
present the real password to the target server, so it must be recoverable. The
point is that a dump of this database no longer hands over every system a user
has connected.

The key lives in CREDENTIALS_KEY. Losing or rotating it makes existing rows
undecryptable, and users would have to re-enter their connections.
"""
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

import backend.core.config  # noqa: F401  -- loads backend/.env before CREDENTIALS_KEY is read


@lru_cache
def _cipher() -> Fernet:
    key = os.getenv("CREDENTIALS_KEY")
    if not key:
        raise RuntimeError(
            "CREDENTIALS_KEY is not set. Generate one with:\n"
            "  python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as e:
        raise RuntimeError("CREDENTIALS_KEY is not a valid Fernet key") from e


def encrypt(value: str) -> str:
    """Encrypt a credential for storage."""
    return _cipher().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Decrypt a stored credential."""
    try:
        return _cipher().decrypt(value.encode()).decode()
    except InvalidToken as e:
        raise ValueError(
            "Stored credential could not be decrypted. The CREDENTIALS_KEY may have "
            "changed, or the row predates encryption."
        ) from e
