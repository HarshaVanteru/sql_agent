# MongoDB Query System Refactoring Summary

## Overview

The MongoDB AI query system has been refactored from a shell-syntax-based architecture to a **structured JSON + PyMongo** architecture. This change eliminates security risks from string-based query execution and provides type safety across the entire pipeline.

### Key Principle: **Never Generate MongoDB Shell Syntax**

The LLM now generates structured JSON queries only. No shell commands, no string parsing, no injection vectors.

---

## Architecture Changes

### Before (Insecure)
```
User Question
    ↓
LLM generates: db.users.find({name: "John"})
    ↓
Validator parses shell syntax with regex
    ↓
Executor regex-extracts args, calls JSON.parse()
    ↓
PyMongo execution
```

**Problems:**
- Shell syntax generation is error-prone
- Regex parsing is fragile
- String manipulation increases injection risk
- No type safety

### After (Secure)
```
User Question
    ↓
LLM generates: {"collection": "users", "operation": "find", "filter": {"name": "John"}}
    ↓
Validator validates JSON against Pydantic models
    ↓
Executor directly calls PyMongo methods with parsed model
    ↓
PyMongo execution
```

**Benefits:**
- Structured JSON is unambiguous
- Pydantic validation ensures type safety at parse time
- No string parsing or regex
- No code execution (eval, exec, subprocess)
- Direct PyMongo calls with validated data

---

## File Changes

### 1. **models.py** (NEW)

**Purpose:** Type-safe MongoDB query representations using Pydantic v2.

**Key Classes:**

#### `MongoQuery` (Base)
- Base model for all queries
- Required fields: `collection`, `operation`
- Validates collection names (alphanumeric + underscore/hyphen)
- Validates operation type (enum)

#### `FindQuery`
- Operation: `find`
- Required: `filter` (dict)
- Optional: `projection`, `sort`, `skip`, `limit`

#### `FindOneQuery`
- Operation: `findOne`
- Required: `filter` (dict)
- Optional: `projection`, `sort`

#### `AggregateQuery`
- Operation: `aggregate`
- Required: `pipeline` (non-empty list of stage dicts)
- Validates each stage is a dict

#### `CountDocumentsQuery`
- Operation: `countDocuments`
- Required: `filter` (dict)

#### `EstimatedDocumentCountQuery`
- Operation: `estimatedDocumentCount`
- No additional required fields

#### `DistinctQuery`
- Operation: `distinct`
- Required: `field` (string), `filter` (dict)

#### `parse_query_json(query_json: str)`
- Parses JSON string into appropriate query model
- Raises `ValueError` if JSON is invalid or doesn't match any model
- Raises `json.JSONDecodeError` if JSON parsing fails

**Type Safety:**
- Uses `Literal` types for operation discrimination
- Pydantic v2 automatic validation at parse time
- Field validators for complex types (operators, stages)

---

### 2. **generation.py** (Refactored)

**Changes:**

#### Prompt Modification
- Changed from shell syntax examples to JSON examples
- Added explicit instruction: "Return ONLY valid JSON"
- Removed all `db.collection.method()` examples
- Added structured query format documentation

#### New Function: `_extract_json_from_response(response_text: str)`
- Extracts JSON from LLM response
- Handles markdown code blocks (```json...```)
- Strips extra whitespace

#### Model Validation
- Validates LLM output as JSON before passing downstream
- Calls `parse_query_json()` to validate against Pydantic models
- Stores both raw JSON string and parsed model in state
- Detects "UNSUPPORTED_QUERY" marker from LLM

#### Error Handling
- Returns clear error messages for JSON parsing failures
- Logs which operation type was detected
- Doesn't pass invalid queries downstream

**State Changes:**
- Added `query_model` field: Pydantic model instance
- Kept `query` field: Raw JSON string (for debugging/logging)
- Removed `query_type` detection (now implicit in model type)

---

### 3. **validation.py** (Refactored - Major Rewrite)

**Key Changes:**

#### No More Shell Parsing
- Removed all regex-based shell syntax extraction
- Removed `db.collection.method()` handling
- Completely model-based validation

#### Operator Validation
- `FILTER_OPERATORS` set: 25 MongoDB filter operators
- `PIPELINE_STAGES` set: 19 aggregation pipeline stages
- Recursive validation of filter objects
- Validates operator names are in allowed set

#### Collection Validation
- `_collection_exists()` checks if collection is in database
- Non-fatal check (doesn't fail if connection is read-only)
- Logs warning if collection not found

#### Execution Plan Validation
- `_explain_query()` uses `collection.find().explain()` for performance hints
- Detects full collection scans (COLLSCAN stage)
- Returns warnings but doesn't fail validation
- Works with both find and aggregate operations

#### Validation Functions
- `_validate_filter_operators(obj: dict)` → Recursive operator validation
- `_validate_pipeline_stages(pipeline: list)` → Pipeline stage validation
- `_collection_exists()` → Collection existence check
- `_explain_query()` → Execution plan analysis

#### State Validation
- Requires `query_model` field (not `query`)
- Increments `retry_count` on validation failure
- Sets `valid=True/False` and `error` message

---

### 4. **execution.py** (Refactored - Major Rewrite)

**Key Principle:** No string parsing, no regex, no eval/exec

#### Direct PyMongo Execution
- Accepts `query_model` (Pydantic instance)
- Calls appropriate PyMongo method based on operation type
- No intermediate JSON parsing or string manipulation

#### Execution Functions
- `_execute_find()` - Uses `collection.find()` with optional projection, sort, skip, limit
- `_execute_find_one()` - Single document with same options
- `_execute_aggregate()` - Direct pipeline execution
- `_execute_count_documents()` - Returns `[{"count": n}]`
- `_execute_estimated_document_count()` - Fast count, no filter
- `_execute_distinct()` - Returns `[{"value": v1}, {"value": v2}, ...]`

#### Type Handling
- `_convert_objectid_to_str()` - Recursively converts BSON ObjectId → JSON string
- Handles nested dicts and lists
- Preserves all other types as-is

#### Result Format
```python
{
    "columns": ["field1", "field2"],
    "rows": [{"field1": value1, "field2": value2}, ...],
    "row_count": N
}
```

**No shell commands, no string queries, no security risks.**

---

### 5. **formatting.py** (Enhanced)

**Changes:**

#### Natural Language Responses
- Distinguishes between query types
- Special handling for count queries → `"Found N document(s)"`
- Special handling for distinct queries → `"Found N unique value(s)"`
- Default → `"Retrieved N document(s)"`

#### Error Handling
- Includes error message in response
- Handles empty result sets gracefully

#### Response Format
```python
{
    "message": "Retrieved 5 document(s).",
    "data": {
        "columns": [...],
        "rows": [...],
        "row_count": 5
    }
}
```

---

### 6. **prompts.py** (Updated)

**Changes:**

#### JSON-Only Instruction
```
"CRITICAL: You MUST return ONLY valid JSON. 
Never generate MongoDB shell syntax (db.collection.find(...))."
```

#### Clear Examples
- find() → JSON with filter, projection, sort, skip, limit
- findOne() → JSON with single document
- aggregate() → JSON with pipeline stages
- countDocuments() → JSON with filter
- estimatedDocumentCount() → JSON with no filter
- distinct() → JSON with field and filter

#### Schema Injection
- Unchanged - still uses `{schema}` placeholder
- Schema fetching works the same way

#### Unsupported Query Marker
```json
{"operation": "UNSUPPORTED_QUERY"}
```

---

### 7. **pipeline.py** (Minor Update)

**Change:**
- Added `query_model` to initial state: `"query_model": None`
- Kept `query` for backward compatibility

**Unchanged:**
- Retry logic
- Conditional routing
- Exception handling
- Logging

---

## Security Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Query Format** | Arbitrary shell strings | Structured JSON only |
| **Parsing** | Regex extraction + JSON parse | Direct Pydantic validation |
| **Code Execution** | String-based (regex, JSON parse) | Type-validated, no strings |
| **Injection Risk** | High (shell syntax) | None (no shell) |
| **Operator Validation** | Partial (post-parse) | Complete (pre-model) |
| **Type Safety** | None | Pydantic v2 |

---

## Backward Compatibility

**Breaking Changes:**
- LLM now requires JSON output, not shell syntax
- Generation agent returns `query_model` in state
- Executor works with `query_model`, not `query` strings
- Validation is stricter (requires valid models)

**Non-Breaking:**
- `run_nosql_pipeline()` API unchanged
- State dict structure similar
- Result format identical
- Error messages compatible

**Migration:**
- Update any custom LLM prompts to generate JSON
- Update any code reading `query_type` (now implicit in model type)
- Update any code directly parsing `query` field (use `query_model` instead)

---

## Testing Recommendations

### Unit Tests

#### Models
```python
# Valid queries
FindQuery(collection="users", filter={"age": {"$gt": 18}})
AggregateQuery(collection="orders", pipeline=[{"$match": {"status": "delivered"}}])

# Invalid queries (should raise)
FindQuery(collection="", filter={})  # Empty collection
FindQuery(collection="users", filter={"$invalid": {}})  # Bad operator
```

#### Generation
```python
# Mock LLM response with JSON
response = generation_agent(state)
assert response["query_model"] is not None
assert isinstance(response["query_model"], FindQuery)
```

#### Execution
```python
# With mock MongoDB
collection.find.return_value = []
state = {"query_model": FindQuery(...), ...}
result = execution_agent(state)
assert result["result"]["row_count"] == 0
```

### Integration Tests

1. End-to-end with real MongoDB
2. Complex aggregation pipelines
3. Edge cases (empty collections, null values, etc.)
4. Error handling (invalid filter operators, missing collections)

---

## Performance Notes

**Same or Better:**
- No regex parsing overhead
- Direct PyMongo calls (no intermediate layer)
- Optional `explain()` for performance hints
- Pydantic validation is fast (compiled)

---

## Monitoring & Logging

**Existing Logging Preserved:**
- Generation agent logs LLM response and parsed type
- Validation agent logs operator/stage validation and explain results
- Execution agent logs operation type and document count
- Formatting agent logs result counts and column names

**New Log Points:**
- `[GENERATION] Valid {operation} query for collection '{name}'`
- `[VALIDATION] {operation} query validated successfully`
- `[EXECUTION] Query executed successfully - returned {count} rows`

---

## Example: Full Query Flow

### User Question
```
"Show me all users over 21 with their emails"
```

### LLM Output (JSON)
```json
{
    "collection": "users",
    "operation": "find",
    "filter": {"age": {"$gt": 21}},
    "projection": {"email": 1, "name": 1}
}
```

### Generation Agent
- Extracts JSON from response
- Calls `parse_query_json()`
- Returns `FindQuery` model in `query_model`
- Stores raw JSON in `query` for logging

### Validation Agent
- Validates `filter` operators: `$gt` is in `FILTER_OPERATORS` ✓
- Validates `projection` is dict ✓
- Validates collection "users" exists ✓
- Runs `explain()` to check execution plan
- Sets `valid=True`

### Execution Agent
- Gets `FindQuery` model
- Calls `collection.find({"age": {"$gt": 21}}).project({"email": 1, "name": 1})`
- Converts ObjectId → string
- Returns `{"columns": ["_id", "name", "email"], "rows": [...], "row_count": 42}`

### Formatting Agent
- Detects regular find query
- Returns: `{"message": "Retrieved 42 document(s).", "data": {...}}`

### User Response
```
"Retrieved 42 document(s). [data with columns and rows]"
```

---

## Future Enhancements

1. **Caching**: Cache schema fetching
2. **Query Logging**: Store executed queries for audit trail
3. **Performance Metrics**: Track query execution time
4. **Field Validation**: Validate filter/projection fields exist in schema
5. **Rate Limiting**: Limit aggregation pipeline depth
6. **Result Pagination**: Support cursor-based pagination
7. **Batch Operations**: Support multiple queries per request

---

## Summary of Security Wins

✓ **No Shell Syntax** - LLM generates JSON only  
✓ **No String Parsing** - Pydantic handles all validation  
✓ **No Code Execution** - No eval, exec, subprocess  
✓ **Type Safe** - Models validated at parse time  
✓ **Operator Whitelist** - Only allowed MongoDB operators  
✓ **Stage Whitelist** - Only allowed pipeline stages  
✓ **Direct PyMongo** - No intermediate layer  

This refactoring transforms the MongoDB query system from a fragile, string-based architecture to a **production-grade, type-safe, secure system** suitable for enterprise use.
