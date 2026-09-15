"""Settings, declared once.

Every environment variable the app reads is a field on `Settings` below. Modules
import `settings` rather than calling os.getenv at import time, so there is a
single answer to "what can be configured" and a single place to change it.

Notably absent: DATABASE_URL. The app has no database of its own -- sessions and
their state live in Redis, and the databases it queries are supplied by whoever
is asking, at runtime.
"""
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, two levels up from this module (backend/app/core/).
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore"
    )

    # ─── Required ────────────────────────────────────────────────────────────
    GROQ_API_KEY: str
    # Signs the session cookie. Changing it logs everyone out, which is a
    # 24-hour inconvenience here rather than a data loss.
    SECRET_KEY: str
    # Encrypts connection passwords before they go into Redis. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    CREDENTIALS_KEY: str

    # ─── Model ───────────────────────────────────────────────────────────────
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # ─── Redis: the only datastore ───────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # Seconds to wait on Redis. Short on purpose: it is on the same network as
    # the app, so slow means broken, and a request waiting on it is a person
    # watching a spinner.
    REDIS_CONNECT_TIMEOUT: float = 2.0
    REDIS_TIMEOUT: float = 3.0
    # Retries per command, over an exponential backoff, before giving up.
    REDIS_RETRIES: int = 2

    # ─── Sessions ────────────────────────────────────────────────────────────
    # 24 hours, fixed from creation rather than sliding: a session is a visit,
    # and a visit has a length.
    SESSION_TTL_SECONDS: int = 86_400
    SESSION_COOKIE_NAME: str = "sql_agent_session"
    # "none" (with SECURE=true) is what a cross-site SPA needs; "lax" is what
    # plain-HTTP localhost needs, because browsers drop SameSite=None without
    # Secure, and Secure without HTTPS.
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_COOKIE_SECURE: bool = False

    # ─── CORS ────────────────────────────────────────────────────────────────
    # Explicit origins, never "*": the spec forbids pairing a wildcard with
    # credentials, and Starlette resolves that pairing by echoing back whichever
    # Origin asked -- every origin, exactly what the wildcard looked like it was
    # avoiding. Cookie sessions make this load-bearing.
    # Kept as a string, not a list[str]: pydantic-settings JSON-decodes complex
    # types straight out of the environment, so a comma-separated value would
    # blow up before any validator could split it. `cors_origins` does the work.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # ─── Agent ───────────────────────────────────────────────────────────────
    AGENT_MAX_ITERATIONS: int = 8
    # Seconds to wait on one model call, and how many times to retry a failed
    # one. A hung call would otherwise hold a threadpool worker for as long as
    # the socket stays open, and there are only so many workers.
    AGENT_LLM_TIMEOUT: float = 60.0
    AGENT_LLM_RETRIES: int = 2
    # Seconds to wait when opening a connection to someone's database, and the
    # ceiling on one query. Without the second, a careless GROUP BY on a large
    # table holds a worker until the database decides it is done.
    DB_CONNECT_TIMEOUT: int = 10
    DB_STATEMENT_TIMEOUT: int = 30
    AGENT_MAX_ROWS: int = 1_000
    AGENT_ROW_SAMPLE: int = 20
    MAX_HISTORY_MESSAGES: int = 20
    ENGINE_CACHE_SIZE: int = 20

    @field_validator("GROQ_API_KEY", "SECRET_KEY")
    @classmethod
    def _not_a_placeholder(cls, value: str, info) -> str:
        """Refuse the example values, which otherwise boot happily and fail later.

        CREDENTIALS_KEY was already checked here; these two were not, so a .env
        copied from .env.example and half filled in started cleanly and then
        failed at the first question with a 401 from Groq -- a long way from
        the line that actually needed editing.
        """
        placeholders = {"your-groq-api-key", "change-me-to-a-long-random-string", "your-fernet-key"}
        if value.strip().lower() in placeholders or not value.strip():
            raise ValueError(
                f"{info.field_name} is still the placeholder from .env.example. "
                + (
                    "Get a key from https://console.groq.com/keys -- it starts with 'gsk_'. "
                    "(Grok from xAI is a different product; its keys will not work here.)"
                    if info.field_name == "GROQ_API_KEY"
                    else 'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
                )
            )
        return value

    @field_validator("CREDENTIALS_KEY")
    @classmethod
    def _usable_fernet_key(cls, value: str) -> str:
        """Reject a bad key now rather than when someone connects a database.

        Checked here because this is the earliest possible moment: settings load
        before the server binds a port, so a placeholder copied out of
        .env.example stops the app at boot with the command that fixes it,
        instead of surfacing as a 500 midway through a visitor's first connect.
        """
        from cryptography.fernet import Fernet

        try:
            Fernet(value.encode())
        except (ValueError, TypeError) as error:
            raise ValueError(
                "CREDENTIALS_KEY is not a valid Fernet key. Generate one with:\n"
                '  python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            ) from error
        return value

    @property
    def cors_origins(self) -> list[str]:
        """CORS_ORIGINS split into the list Starlette wants."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def _load() -> Settings:
    return Settings()


settings = _load()
