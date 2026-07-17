"""Pydantic schemas for query operations."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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


class MessageResponse(BaseModel):
    """One stored turn, as it can be replayed to the user."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    # Assistant turns that ran a query: the SQL, and the columns/rows/row_count
    # the user was shown. Null on user turns and query-less replies.
    sql_query: str | None = None
    result: dict | None = None
    created_at: datetime


class ConversationSummary(BaseModel):
    """A conversation without its messages, for listing."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]
    total: int


class ConversationDetailResponse(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]
