"""Pydantic schemas for the signup module."""
from __future__ import annotations

import re

from pydantic import BaseModel, field_validator


def validate_email(v: str) -> str:
    v = v.strip().lower()
    if len(v) > 255:
        raise ValueError("Email must be at most 255 characters.")
    if not re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", v):
        raise ValueError("Enter a valid email address.")
    return v


def validate_password(v: str) -> str:
    if len(v) < 8 or len(v) > 128:
        raise ValueError(
            "Password must be at least 8 characters and contain one uppercase letter, "
            "one number, and one special character (!@#$%^&*)."
        )
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*]", v):
        raise ValueError(
            "Password must contain at least one special character from: !@#$%^&*"
        )
    if re.search(r"\s", v):
        raise ValueError("Password must not contain spaces.")
    return v


def validate_name(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Name must be at least 1 character.")
    if len(v) > 50:
        raise ValueError("Name must be at most 50 characters.")
    if not re.fullmatch(r"[A-Za-z\s\-']+", v):
        raise ValueError(
            "Name may only contain letters, spaces, hyphens, and apostrophes."
        )
    return v


class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, v: str) -> str:
        return validate_email(v)

    @field_validator("password", mode="before")
    @classmethod
    def _password(cls, v: str) -> str:
        return validate_password(v)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def _name(cls, v: str) -> str:
        return validate_name(v)


class SignupResponse(BaseModel):
    user_id: str   # UUID of the newly created user
    message: str
