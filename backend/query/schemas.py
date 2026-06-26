"""Pydantic schemas for query operations."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    columns: list[str]
    rows: list[dict]
    row_count: int


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class NaturalLanguageQueryResponse(BaseModel):
    sql: str | None = None
    query: str | None = None
    query_type: str | None = None
    columns: list[str]
    rows: list[dict]
    row_count: int
