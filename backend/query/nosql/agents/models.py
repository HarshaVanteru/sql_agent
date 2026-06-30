"""MongoDB query models using Pydantic for type-safe validation."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class MongoQuery(BaseModel):
    """Base model for all MongoDB queries."""

    collection: str = Field(..., min_length=1, description="MongoDB collection name")
    operation: str = Field(..., description="MongoDB operation type")

    class Config:
        extra = "forbid"

    @field_validator("collection")
    @classmethod
    def validate_collection_name(cls, v: str) -> str:
        """Validate collection name is not empty and contains valid characters."""
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid collection name: {v}")
        return v

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation is one of the allowed types."""
        allowed = {"find", "findOne", "aggregate", "countDocuments", "estimatedDocumentCount", "distinct"}
        if v not in allowed:
            raise ValueError(f"Operation must be one of {allowed}, got: {v}")
        return v


class FindQuery(MongoQuery):
    """Model for find operations."""

    operation: Literal["find"] = Field(default="find", description="Operation type")
    filter: Dict[str, Any] = Field(default_factory=dict, description="MongoDB filter document")
    projection: Optional[Dict[str, int]] = Field(default=None, description="Fields to include/exclude")
    sort: Optional[Dict[str, int]] = Field(default=None, description="Sort order")
    skip: Optional[int] = Field(default=None, ge=0, description="Number of documents to skip")
    limit: Optional[int] = Field(default=None, gt=0, description="Maximum documents to return")

    @field_validator("projection", "sort", mode="before")
    @classmethod
    def validate_dict_field(cls, v: Any) -> Optional[Dict[str, int]]:
        """Validate projection and sort are dictionaries."""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError(f"Expected dict, got {type(v).__name__}")
        return v


class FindOneQuery(MongoQuery):
    """Model for findOne operations."""

    operation: Literal["findOne"] = Field(default="findOne", description="Operation type")
    filter: Dict[str, Any] = Field(default_factory=dict, description="MongoDB filter document")
    projection: Optional[Dict[str, int]] = Field(default=None, description="Fields to include/exclude")
    sort: Optional[Dict[str, int]] = Field(default=None, description="Sort order")

    @field_validator("projection", "sort", mode="before")
    @classmethod
    def validate_dict_field(cls, v: Any) -> Optional[Dict[str, int]]:
        """Validate projection and sort are dictionaries."""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError(f"Expected dict, got {type(v).__name__}")
        return v


class AggregateQuery(MongoQuery):
    """Model for aggregation pipeline operations."""

    operation: Literal["aggregate"] = Field(default="aggregate", description="Operation type")
    pipeline: List[Dict[str, Any]] = Field(..., min_length=1, description="Aggregation pipeline stages")

    @field_validator("pipeline")
    @classmethod
    def validate_pipeline(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate pipeline is a list of stage dictionaries."""
        if not isinstance(v, list):
            raise ValueError(f"Pipeline must be a list, got {type(v).__name__}")
        if not v:
            raise ValueError("Pipeline cannot be empty")
        for idx, stage in enumerate(v):
            if not isinstance(stage, dict):
                raise ValueError(f"Stage {idx} must be a dict, got {type(stage).__name__}")
            if not stage:
                raise ValueError(f"Stage {idx} cannot be empty")
        return v


class CountDocumentsQuery(MongoQuery):
    """Model for countDocuments operations."""

    operation: Literal["countDocuments"] = Field(default="countDocuments", description="Operation type")
    filter: Dict[str, Any] = Field(default_factory=dict, description="MongoDB filter document")


class EstimatedDocumentCountQuery(MongoQuery):
    """Model for estimatedDocumentCount operations."""

    operation: Literal["estimatedDocumentCount"] = Field(
        default="estimatedDocumentCount", description="Operation type"
    )


class DistinctQuery(MongoQuery):
    """Model for distinct operations."""

    operation: Literal["distinct"] = Field(default="distinct", description="Operation type")
    field: str = Field(..., min_length=1, description="Field name for distinct values")
    filter: Dict[str, Any] = Field(default_factory=dict, description="MongoDB filter document")


# Union type for all query types
QueryType = (
    FindQuery
    | FindOneQuery
    | AggregateQuery
    | CountDocumentsQuery
    | EstimatedDocumentCountQuery
    | DistinctQuery
)


def parse_query_json(query_json: str) -> QueryType:
    """
    Parse a JSON string into a validated MongoDB query model.

    Args:
        query_json: JSON string representing a MongoDB query

    Returns:
        Validated query model instance

    Raises:
        ValueError: If JSON is invalid or doesn't match any query model
        json.JSONDecodeError: If JSON parsing fails
    """
    import json

    data = json.loads(query_json)

    if not isinstance(data, dict):
        raise ValueError(f"Query must be a JSON object, got {type(data).__name__}")

    operation = data.get("operation")

    # Map operation to model class
    model_map = {
        "find": FindQuery,
        "findOne": FindOneQuery,
        "aggregate": AggregateQuery,
        "countDocuments": CountDocumentsQuery,
        "estimatedDocumentCount": EstimatedDocumentCountQuery,
        "distinct": DistinctQuery,
    }

    model_class = model_map.get(operation)
    if not model_class:
        raise ValueError(
            f"Unknown operation '{operation}'. Allowed: {list(model_map.keys())}"
        )

    try:
        return model_class(**data)
    except Exception as e:
        raise ValueError(f"Failed to parse query as {model_class.__name__}: {str(e)}")
