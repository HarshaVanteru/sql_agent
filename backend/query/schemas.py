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
    # Omit to start a new conversation; the response returns the new id.
    conversation_id: str | None = None


class NaturalLanguageQueryResponse(BaseModel):
    # None when the agent answered without needing data; `message` carries the reply.
    query: str | None = None
    columns: list[str]
    rows: list[dict]
    row_count: int
    conversation_id: str | None = None
    # The agent's reply when it answered without data (a greeting or refusal).
    message: str | None = None
