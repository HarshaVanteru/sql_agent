"""Test fixtures, and the environment the app needs before it can be imported.

The environment has to be set here, at the top of the file, rather than in a
fixture: `app.core.config` builds its `settings` singleton at import time, so by
the time any fixture runs it is already too late. CI has no backend/.env -- it
is gitignored -- so without this every test that imports the app would fail on
a missing GROQ_API_KEY rather than on anything it meant to check.

Real values in the environment still win: these are `setdefault`.
"""
import os

from cryptography.fernet import Fernet

os.environ.setdefault("GROQ_API_KEY", "gsk_test_key_not_a_real_one")
os.environ.setdefault("SECRET_KEY", "test-secret-key-long-enough-to-not-be-a-placeholder")
os.environ.setdefault("CREDENTIALS_KEY", Fernet.generate_key().decode())
# Nothing should reach a real Redis, and a test that tries should fail fast
# rather than quietly talk to the developer's own instance.
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:1/0")
# Console output from logfire would bury the pytest report.
os.environ.setdefault("LOGFIRE_CONSOLE", "false")

import fakeredis.aioredis  # noqa: E402
import pytest  # noqa: E402

# A port on which nothing listens, so connecting to it is refused immediately.
# This is what the startup and readiness tests point Redis at.
UNREACHABLE_REDIS_URL = "redis://127.0.0.1:1/0"


@pytest.fixture
def anyio_backend() -> str:
    """Run `@pytest.mark.anyio` tests on asyncio only, not also on trio."""
    return "asyncio"


@pytest.fixture
def fake_redis():
    """An in-memory Redis speaking the real client's API, including expiries."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def logged(monkeypatch):
    """Capture what the app logs, so a test can assert on what it claimed.

    Returns a list of the rendered message templates. The startup logging is
    the behaviour under test in test_startup.py, so it needs to be observable.
    """
    import logfire

    messages: list[tuple[str, str]] = []

    def record(level: str):
        def log(template: str, *_args, **_kwargs) -> None:
            messages.append((level, template))

        return log

    for level in ("info", "warning", "error", "exception"):
        monkeypatch.setattr(logfire, level, record(level))
    return messages
