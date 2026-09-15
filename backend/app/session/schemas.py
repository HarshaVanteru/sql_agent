"""Session request and response shapes."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SessionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Trim, and reject a name that was only whitespace.

        min_length alone lets "   " through, which would name the session after
        nobody and slug its id to "guest".
        """
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Name cannot be blank")
        return trimmed


class SessionResponse(BaseModel):
    session_id: str
    name: str
    created_at: datetime
    expires_at: datetime
    connection_count: int = 0
