"""Encryption for stored connected-database credentials.

These passwords are reversibly encrypted rather than hashed: the agent has to
present the real password to the target server, so it must be recoverable. The
point is that a dump of Redis does not hand over every system someone
has connected.

The key lives in CREDENTIALS_KEY. Losing or rotating it makes stored
connections undecryptable, and they would have to be re-entered.
"""
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache
def _cipher() -> Fernet:
    key = settings.CREDENTIALS_KEY
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
            "Stored credential could not be decrypted. The CREDENTIALS_KEY may "
            "have changed since the session was created."
        ) from e
