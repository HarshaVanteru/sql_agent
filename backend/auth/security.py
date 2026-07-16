"""Password hashing and JWT handling."""
from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

import backend.config  # noqa: F401  -- loads backend/.env before SECRET_KEY is read

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

BCRYPT_ROUNDS = 12
MIN_PASSWORD_LENGTH = 8


def hash_password(plain: str) -> str:
    # bcrypt silently truncates at 72 bytes; reject rather than accept a password
    # whose tail is ignored.
    if len(plain.encode()) > 72:
        raise ValueError("Password must be at most 72 bytes")
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def create_access_token(user_id: str) -> str:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Return the user id in `token`, or raise ValueError if it isn't usable."""
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("expired" if "expired" in str(exc).lower() else "invalid") from exc
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("invalid")
    return user_id


def generate_refresh_token() -> tuple[str, str]:
    """Return (raw token, sha256 hash). Only the hash is stored."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def refresh_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
