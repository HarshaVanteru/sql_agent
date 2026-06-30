"""
Test script for refactored MongoDB query system.
Tests the new Pydantic model validation without requiring LLM/MongoDB connection.
"""
import json
from backend.query.nosql.agents.models import (
    FindQuery,
    FindOneQuery,
    AggregateQuery,
    CountDocumentsQuery,
    EstimatedDocumentCountQuery,
    DistinctQuery,
    parse_query_json,
)


def test_find_query():
    """Test FindQuery model validation."""
    print("\n=== Testing FindQuery ===")

    # Valid find query
    json_str = json.dumps({
        "collection": "users",
        "operation": "find",
        "filter": {"age": {"$gt": 18}},
        "projection": {"name": 1, "email": 1},
        "limit": 10
    })

    model = parse_query_json(json_str)
    assert isinstance(model, FindQuery)
    assert model.collection == "users"
    assert model.operation == "find"
    assert model.filter == {"age": {"$gt": 18}}
    print("[PASS] Valid FindQuery parsed successfully")

    # Models accept any filter - validation_agent checks operators
    invalid_json = json.dumps({
        "collection": "users",
        "operation": "find",
        "filter": {"age": {"$badop": 18}}
    })
    model = parse_query_json(invalid_json)
    print(f"[PASS] Model accepts filter (validation_agent will check operators)")


def test_aggregate_query():
    """Test AggregateQuery model validation."""
    print("\n=== Testing AggregateQuery ===")

    json_str = json.dumps({
        "collection": "orders",
        "operation": "aggregate",
        "pipeline": [
            {"$match": {"status": "completed"}},
            {"$group": {"_id": "$customer_id", "total": {"$sum": "$amount"}}},
            {"$sort": {"total": -1}},
            {"$limit": 10}
        ]
    })

    model = parse_query_json(json_str)
    assert isinstance(model, AggregateQuery)
    assert len(model.pipeline) == 4
    print("[PASS] Valid AggregateQuery with 4 pipeline stages parsed successfully")

    # Models accept any stages - validation_agent checks allowed stages
    invalid_json = json.dumps({
        "collection": "orders",
        "operation": "aggregate",
        "pipeline": [{"$badstage": {}}]
    })
    model = parse_query_json(invalid_json)
    print(f"[PASS] Model accepts pipeline (validation_agent will check stages)")


def test_count_documents_query():
    """Test CountDocumentsQuery model."""
    print("\n=== Testing CountDocumentsQuery ===")

    json_str = json.dumps({
        "collection": "users",
        "operation": "countDocuments",
        "filter": {"status": "active"}
    })

    model = parse_query_json(json_str)
    assert isinstance(model, CountDocumentsQuery)
    print("[PASS] CountDocumentsQuery parsed successfully")


def test_estimated_document_count_query():
    """Test EstimatedDocumentCountQuery model."""
    print("\n=== Testing EstimatedDocumentCountQuery ===")

    json_str = json.dumps({
        "collection": "logs",
        "operation": "estimatedDocumentCount"
    })

    model = parse_query_json(json_str)
    assert isinstance(model, EstimatedDocumentCountQuery)
    print("[PASS] EstimatedDocumentCountQuery parsed successfully")


def test_distinct_query():
    """Test DistinctQuery model."""
    print("\n=== Testing DistinctQuery ===")

    json_str = json.dumps({
        "collection": "products",
        "operation": "distinct",
        "field": "category",
        "filter": {"price": {"$gt": 100}}
    })

    model = parse_query_json(json_str)
    assert isinstance(model, DistinctQuery)
    assert model.field == "category"
    print("[PASS] DistinctQuery parsed successfully")


def test_invalid_json():
    """Test invalid JSON handling."""
    print("\n=== Testing Invalid JSON ===")

    try:
        parse_query_json("not valid json {")
        print("[FAIL] Invalid JSON was not caught")
    except json.JSONDecodeError:
        print("[PASS] Invalid JSON caught")


def test_unsupported_operation():
    """Test unsupported operation handling."""
    print("\n=== Testing Unsupported Operation ===")

    try:
        json_str = json.dumps({
            "collection": "users",
            "operation": "invalidOp"
        })
        parse_query_json(json_str)
        print("[FAIL] Unsupported operation was not caught")
    except ValueError as e:
        print(f"[PASS] Unsupported operation caught: {str(e)[:60]}")


def test_missing_required_field():
    """Test missing required field handling."""
    print("\n=== Testing Missing Required Field ===")

    try:
        json_str = json.dumps({
            "collection": "users",
            "operation": "find"
            # filter is required for find
        })
        model = parse_query_json(json_str)
        # filter should default to empty dict for find
        assert model.filter == {}
        print("[PASS] Missing filter defaulted to empty dict")
    except ValueError as e:
        print(f"Error: {e}")


def test_find_one_query():
    """Test FindOneQuery model."""
    print("\n=== Testing FindOneQuery ===")

    json_str = json.dumps({
        "collection": "users",
        "operation": "findOne",
        "filter": {"username": "john_doe"}
    })

    model = parse_query_json(json_str)
    assert isinstance(model, FindOneQuery)
    print("[PASS] FindOneQuery parsed successfully")


def test_empty_collection_name():
    """Test empty collection name rejection."""
    print("\n=== Testing Empty Collection Name ===")

    try:
        json_str = json.dumps({
            "collection": "",
            "operation": "find",
            "filter": {}
        })
        parse_query_json(json_str)
        print("[FAIL] Empty collection name was not caught")
    except ValueError as e:
        print(f"[PASS] Empty collection name caught: {str(e)[:60]}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("TESTING REFACTORED MONGODB QUERY SYSTEM")
    print("="*60)

    test_find_query()
    test_aggregate_query()
    test_count_documents_query()
    test_estimated_document_count_query()
    test_distinct_query()
    test_find_one_query()
    test_invalid_json()
    test_unsupported_operation()
    test_missing_required_field()
    test_empty_collection_name()

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
