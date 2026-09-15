"""Shapes for the databases a visitor connects."""
from datetime import datetime

from pydantic import BaseModel, Field


class ConnectionCredentialInput(BaseModel):
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    database_name: str = Field(min_length=1)


class ConnectionCredentialOut(BaseModel):
    """Credentials as returned to the client.

    The password is deliberately absent: it is encrypted at rest and there is no
    reason to hand it back out.
    """

    host: str
    port: int
    username: str
    database_name: str


class ConnectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    db_type: str = Field(min_length=1, max_length=50)
    credentials: ConnectionCredentialInput


class ConnectionResponse(BaseModel):
    id: str
    name: str
    db_type: str
    created_at: datetime


class ConnectionDetailResponse(ConnectionResponse):
    credentials: ConnectionCredentialOut


class ConnectionListResponse(BaseModel):
    connections: list[ConnectionResponse]
    total: int
