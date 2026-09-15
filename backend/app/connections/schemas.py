"""Shapes for the databases a visitor connects."""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.core.validators import Host, RequiredText
from app.query.databases.connections import SUPPORTED_DB_TYPES

# Constrained at the edge rather than deep in the service: a typo in the engine
# name is a bad request, and the reply should say which names are real.
DatabaseType = Annotated[
    str,
    Field(
        description=f"One of: {', '.join(sorted(SUPPORTED_DB_TYPES))}",
        json_schema_extra={"enum": sorted(SUPPORTED_DB_TYPES)},
    ),
]


class ConnectionCredentialInput(BaseModel):
    host: Host
    port: int = Field(ge=1, le=65535)
    username: RequiredText("User", 255)  # type: ignore[valid-type]
    # Optional, unlike every other field here: public read-only databases are
    # commonly published with a username and no password at all.
    password: str = Field(default="", max_length=1024)
    database_name: RequiredText("Database", 255)  # type: ignore[valid-type]


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
    name: RequiredText("Name", 255)  # type: ignore[valid-type]
    db_type: DatabaseType
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
