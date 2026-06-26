"""Pydantic schemas for database management."""
from pydantic import BaseModel, Field


class DatabaseCredentialInput(BaseModel):
    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    database_name: str = Field(..., min_length=1)


class DatabaseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    db_type: str = Field(..., min_length=1, max_length=50)
    credentials: DatabaseCredentialInput


class DatabaseResponse(BaseModel):
    id: str
    name: str
    db_type: str
    created_at: str

    class Config:
        from_attributes = True


class DatabaseDetailResponse(DatabaseResponse):
    credentials: DatabaseCredentialInput

    class Config:
        from_attributes = True


class DatabaseListResponse(BaseModel):
    databases: list[DatabaseResponse]
    total: int
