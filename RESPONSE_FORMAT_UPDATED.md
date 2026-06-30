# Updated Response Format - With Final Query

The system now includes the final generated query in all responses, giving you complete visibility into what was generated and executed.

## Response Structure

All responses now include:
- `status` - "success" or "error"
- `message` - Human-readable message
- `valid` - Whether query was valid
- `query` - The final generated JSON query
- `data` - MongoDB results (if successful)
- `retry_count` - Number of retries (if failed)

---

## Example Responses

### Success: Find Query

**User Question:** "Show me all users"

**Response:**
```json
{
    "status": "success",
    "message": "Retrieved 42 document(s).",
    "valid": true,
    "query": {
        "collection": "users",
        "operation": "find",
        "filter": {}
    },
    "data": {
        "columns": ["_id", "name", "email"],
        "rows": [
            {
                "_id": "507f1f77bcf86cd799439011",
                "name": "John Doe",
                "email": "john@example.com"
            },
            ...
        ],
        "row_count": 42
    }
}
```

---

### Success: Count Query

**User Question:** "Count users older than 21"

**Response:**
```json
{
    "status": "success",
    "message": "Found 157 document(s).",
    "valid": true,
    "query": {
        "collection": "users",
        "operation": "countDocuments",
        "filter": {
            "age": {
                "$gt": 21
            }
        }
    },
    "data": {
        "columns": ["count"],
        "rows": [
            {
                "count": 157
            }
        ],
        "row_count": 1
    }
}
```

---

### Success: Aggregate Query

**User Question:** "Get total sales per customer"

**Response:**
```json
{
    "status": "success",
    "message": "Retrieved 128 document(s).",
    "valid": true,
    "query": {
        "collection": "orders",
        "operation": "aggregate",
        "pipeline": [
            {
                "$group": {
                    "_id": "$customer_id",
                    "total": {
                        "$sum": "$amount"
                    }
                }
            },
            {
                "$sort": {
                    "total": -1
                }
            }
        ]
    },
    "data": {
        "columns": ["_id", "total"],
        "rows": [
            {
                "_id": "507f1f77bcf86cd799439011",
                "total": 15000
            },
            ...
        ],
        "row_count": 128
    }
}
```

---

### Error: Unsupported Query

**User Question:** "list collections"

**Response:**
```json
{
    "status": "error",
    "message": "Error executing query: Query is not supported by the system",
    "valid": false,
    "retry_count": 2,
    "query": {
        "operation": "UNSUPPORTED_QUERY"
    }
}
```

---

### Error: Invalid Query

**User Question:** "Show me all documents where age equals apple"

**Response:**
```json
{
    "status": "error",
    "message": "Error executing query: Unknown operator: $invalidOp",
    "valid": false,
    "retry_count": 2,
    "query": {
        "collection": "users",
        "operation": "find",
        "filter": {
            "age": {
                "$invalidOp": "apple"
            }
        }
    }
}
```

---

### Error: Collection Not Found

**User Question:** "Get all documents from nonexistent_collection"

**Response:**
```json
{
    "status": "error",
    "message": "Error executing query: Collection 'nonexistent_collection' not found",
    "valid": false,
    "retry_count": 2,
    "query": {
        "collection": "nonexistent_collection",
        "operation": "find",
        "filter": {}
    }
}
```

---

### Empty Results

**User Question:** "Find users named Nonexistent"

**Response:**
```json
{
    "status": "success",
    "message": "No results found.",
    "valid": true,
    "data": {
        "columns": [],
        "rows": [],
        "row_count": 0
    },
    "query": {
        "collection": "users",
        "operation": "find",
        "filter": {
            "name": "Nonexistent"
        }
    }
}
```

---

## Key Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `message` | string | Human-readable summary |
| `valid` | boolean | Whether query passed validation |
| `query` | object | The final generated MongoDB query (JSON) |
| `data` | object | Result rows, columns, and count (success only) |
| `retry_count` | number | How many retries were attempted (error only) |

---

## Benefits

✓ **Complete Visibility** - See exactly what query was generated  
✓ **Audit Trail** - Track which queries were attempted  
✓ **Debugging** - Understand why queries failed  
✓ **Validation** - Confirm the LLM generated correct JSON  
✓ **User Feedback** - Show users what was executed  

---

## Logging

The pipeline logs the final query with operation and collection:

```
[PIPELINE END] Valid: true, Operation: find, Collection: users
[PIPELINE END] Query: {"collection": "users", "operation": "find", ...}
[PIPELINE END] Error: None
[PIPELINE END] Retry Count: 0
[PIPELINE END] Result: 42 rows returned
```

---

## Usage Example

```python
from backend.query.nosql.pipeline import run_nosql_pipeline

result = run_nosql_pipeline(
    question="Show me users over 21",
    connection=mongodb_client,
    database_name="mydb"
)

# Access the response
response = result["response"]

print(f"Status: {response['status']}")
print(f"Message: {response['message']}")
print(f"Query: {response['query']}")

if response['status'] == 'success':
    data = response['data']
    print(f"Rows: {data['row_count']}")
    for row in data['rows']:
        print(row)
else:
    print(f"Error: {response['message']}")
    print(f"Retries: {response['retry_count']}")
```

---

## Backward Compatibility

The response structure is backward compatible:

**Old code expecting:**
```python
result["response"]["message"]  # Still works!
result["response"]["data"]     # Still works!
```

**New code can access:**
```python
result["response"]["status"]   # New field
result["response"]["query"]    # New field
result["response"]["valid"]    # New field
```

---

## Migration Guide

If you're parsing responses in frontend/API code:

**Before:**
```python
if result["response"]:
    rows = result["response"].get("rows", [])
```

**After (Better):**
```python
if result["response"]["status"] == "success":
    rows = result["response"]["data"].get("rows", [])
    query = result["response"]["query"]
else:
    error = result["response"]["message"]
```

---

This update provides complete transparency into the query generation and execution process!
