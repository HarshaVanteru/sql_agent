# Updated Response Format - LLM Response + Final Executable Query

The response now includes:
- `llm_response` - Raw LLM generated JSON string
- `query` - Final executable MongoDB query (shell syntax)
- `query_json` - Parsed JSON structure

---

## Response Structure

```json
{
    "status": "success|error",
    "message": "Human readable message",
    "valid": true/false,
    "retry_count": 0,
    "llm_response": "Raw JSON from LLM",
    "query": "db.collection.method(...)",
    "query_json": { JSON structure },
    "data": { results }
}
```

---

## Example 1: Find All Users

### Flow
```
1. User Question: "Show all users"
                  ↓
2. LLM Response: {"collection": "users", "operation": "find", "filter": {}, "limit": 100}
                  ↓
3. Parsed JSON: {collection, operation, filter, limit}
                  ↓
4. Final Query: db.users.find({}).limit(100)
                  ↓
5. Execute & Return Results
```

### Response

```json
{
    "status": "success",
    "message": "Retrieved 3 document(s).",
    "valid": true,
    "retry_count": 0,
    
    "llm_response": "{\"collection\": \"users\", \"operation\": \"find\", \"filter\": {}, \"limit\": 100}",
    
    "query": "db.users.find({}).limit(100)",
    
    "query_json": {
        "collection": "users",
        "operation": "find",
        "filter": {},
        "limit": 100
    },
    
    "data": {
        "columns": ["_id", "name", "email", "password_hash", "role", "created_at"],
        "rows": [
            {
                "_id": "69afff70e2219633d2964226",
                "name": "Harsha",
                "email": "Harsha@gmail.com",
                "password_hash": "$2b$12$...",
                "role": "user",
                "created_at": "2026-03-10T11:24:32.185000"
            },
            {
                "_id": "69b10e78063e14aa724f7444",
                "name": "user1",
                "email": "user1@gamil.com",
                "password_hash": "$2b$12$...",
                "role": "user",
                "created_at": "2026-03-11T06:40:56.572000"
            },
            {
                "_id": "69b10eea063e14aa724f7445",
                "name": "user2",
                "email": "user2@gmail.com",
                "password_hash": "$2b$12$...",
                "role": "user",
                "created_at": "2026-03-11T06:42:50.439000"
            }
        ],
        "row_count": 3
    }
}
```

### UI Display

```
Generated MongoDB Query:
db.users.find({}).limit(100)

Results: 3 row(s)

_id                      | name   | email              | role | created_at
69afff70e2219633d2964226 | Harsha | Harsha@gmail.com   | user | 2026-03-10
69b10e78063e14aa724f7444 | user1  | user1@gamil.com    | user | 2026-03-11
69b10eea063e14aa724f7445 | user2  | user2@gmail.com    | user | 2026-03-11
```

---

## Example 2: Count Query

### Response

```json
{
    "status": "success",
    "message": "Found 157 document(s).",
    "valid": true,
    "retry_count": 0,
    
    "llm_response": "{\"collection\": \"users\", \"operation\": \"countDocuments\", \"filter\": {\"age\": {\"$gt\": 18}}}",
    
    "query": "db.users.countDocuments({ age: { $gt: 18 } })",
    
    "query_json": {
        "collection": "users",
        "operation": "countDocuments",
        "filter": {
            "age": {
                "$gt": 18
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

### UI Display

```
Generated MongoDB Query:
db.users.countDocuments({ age: { $gt: 18 } })

Result: 157 documents found
```

---

## Example 3: Aggregation Query

### Response

```json
{
    "status": "success",
    "message": "Retrieved 5 document(s).",
    "valid": true,
    "retry_count": 0,
    
    "llm_response": "{\"collection\": \"orders\", \"operation\": \"aggregate\", \"pipeline\": [{\"$group\": {\"_id\": \"$customer_id\", \"total\": {\"$sum\": \"$amount\"}}}]}",
    
    "query": "db.orders.aggregate([ { $group: { _id: \"$customer_id\", total: { $sum: \"$amount\" } } } ])",
    
    "query_json": {
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
            }
        ]
    },
    
    "data": {
        "columns": ["_id", "total"],
        "rows": [
            {
                "_id": "cust_001",
                "total": 15000
            },
            {
                "_id": "cust_002",
                "total": 12500
            },
            ...
        ],
        "row_count": 5
    }
}
```

### UI Display

```
Generated MongoDB Query:
db.orders.aggregate([ { $group: { _id: "$customer_id", total: { $sum: "$amount" } } } ])

Results: 5 row(s)

_id      | total
cust_001 | 15000
cust_002 | 12500
...
```

---

## Example 4: Error Response

### Response

```json
{
    "status": "error",
    "message": "Error executing query: Query is not supported by the system",
    "valid": false,
    "retry_count": 2,
    
    "llm_response": "{\"operation\": \"UNSUPPORTED_QUERY\"}",
    
    "query": null,
    
    "query_json": {
        "operation": "UNSUPPORTED_QUERY"
    }
}
```

### UI Display

```
Error: Query is not supported by the system
(Retries: 2)

LLM Response: {"operation": "UNSUPPORTED_QUERY"}
```

---

## Response Field Reference

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `status` | string | "success" or "error" | Query execution status |
| `message` | string | "Retrieved 3 documents" | Human-readable result summary |
| `valid` | boolean | true | Whether query passed validation |
| `retry_count` | number | 0 | Number of retries (on error only) |
| **`llm_response`** | string | JSON string | **Raw output from LLM** |
| **`query`** | string | "db.users.find({})" | **Final executable MongoDB query** |
| `query_json` | object | {collection, operation, ...} | Parsed JSON structure for reference |
| `data` | object | {columns, rows, row_count} | Query results (success only) |

---

## Using the Response Fields

### For UI Display

```javascript
// Show the MongoDB query that was executed
const mongoQuery = response.query;
console.log("Generated MongoDB Query:", mongoQuery);
// Output: db.users.find({}).limit(100)

// Show the results in a table
const tableData = response.data.rows;
const columns = response.data.columns;
```

### For Audit/Logging

```javascript
// Log what the LLM generated
console.log("LLM Generated:", response.llm_response);
// Output: {"collection": "users", "operation": "find", ...}

// Log what query was actually executed
console.log("Executed Query:", response.query);
// Output: db.users.find({}).limit(100)
```

### For Debugging

```javascript
if (response.status === 'error') {
    console.log("Error:", response.message);
    console.log("LLM Response:", response.llm_response);
    console.log("Retries Attempted:", response.retry_count);
}
```

### Copy-Paste to MongoDB

```bash
# Users can directly copy the `query` field and run it in MongoDB shell
$ mongo
> db.users.find({}).limit(100)
```

---

## React Component Example

```jsx
function QueryResponse({ response }) {
  return (
    <div className="query-response">
      {/* Show the executable query */}
      <div className="query-display">
        <h3>Generated MongoDB Query:</h3>
        <code className="mongodb-shell">
          {response.query}
        </code>
        <button onClick={() => copyToClipboard(response.query)}>
          Copy Query
        </button>
      </div>

      {/* Show LLM's raw response for reference */}
      <details>
        <summary>LLM Response (Raw)</summary>
        <pre>{response.llm_response}</pre>
      </details>

      {/* Show results */}
      {response.status === 'success' && (
        <div className="results">
          <h3>Results: {response.data.row_count} row(s)</h3>
          <ResultsTable 
            columns={response.data.columns}
            rows={response.data.rows}
          />
        </div>
      )}

      {/* Show error */}
      {response.status === 'error' && (
        <div className="error">
          <p>{response.message}</p>
          <p>Retries: {response.retry_count}</p>
        </div>
      )}
    </div>
  );
}
```

---

## Summary

### Three Query Representations

1. **`llm_response`** - What the LLM generated (raw JSON string)
   ```json
   {"collection": "users", "operation": "find", ...}
   ```

2. **`query`** - Final executable MongoDB query (shell syntax)
   ```javascript
   db.users.find({}).limit(100)
   ```

3. **`query_json`** - Parsed JSON structure (reference)
   ```json
   {"collection": "users", "operation": "find", ...}
   ```

### Use Cases

- **Display in UI** → Use `response.query` (MongoDB shell syntax)
- **Copy-Paste to MongoDB** → Use `response.query`
- **Audit Trail** → Log both `llm_response` and `query`
- **Debugging** → Check `llm_response` to see what LLM generated
- **Building Queries Programmatically** → Use `query_json`

---

**The response now provides complete transparency into the query generation and execution process!** ✅
