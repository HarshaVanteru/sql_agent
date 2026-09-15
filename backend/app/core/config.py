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
    AGENT_MAX_ROWS: int = 1_000
    AGENT_ROW_SAMPLE: int = 20
    MAX_HISTORY_MESSAGES: int = 20
    ENGINE_CACHE_SIZE: int = 20

    @property
    def cors_origins(self) -> list[str]:
        """CORS_ORIGINS split into the list Starlette wants."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def _load() -> Settings:
    return Settings()


settings = _load()
