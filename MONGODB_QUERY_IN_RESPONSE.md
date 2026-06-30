# MongoDB Query in Response - UI Display Format

The system now includes the **final MongoDB shell query** in all responses for easy display in the UI.

---

## Response Structure

All responses now include:
- `status` - "success" or "error"
- `message` - Human-readable message
- `valid` - Whether query was valid
- `mongodb_query` - **Final executable MongoDB query** (db.collection.method(...))
- `query` - Original JSON structure (for reference)
- `data` - MongoDB results (if successful)

---

## Examples

### Find All Users

**Request:** "Show all users"

**Response:**
```json
{
    "status": "success",
    "message": "Retrieved 3 document(s).",
    "valid": true,
    "mongodb_query": "db.users.find({}).limit(100)",
    "query": {
        "collection": "users",
        "operation": "find",
        "filter": {},
        "limit": 100
    },
    "data": {
        "columns": ["_id", "name", "email"],
        "rows": [
            {
                "_id": "69afff70e2219633d2964226",
                "name": "Harsha",
                "email": "Harsha@gmail.com"
            },
            {
                "_id": "69b10e78063e14aa724f7444",
                "name": "user1",
                "email": "user1@gamil.com"
            },
            {
                "_id": "69b10eea063e14aa724f7445",
                "name": "user2",
                "email": "user2@gmail.com"
            }
        ],
        "row_count": 3
    }
}
```

**UI Display:**
```
Generated MongoDB Query:
db.users.find({}).limit(100)

Results: 3 row(s)
_id                      | name   | email
69afff70e2219633d2964226 | Harsha | Harsha@gmail.com
69b10e78063e14aa724f7444 | user1  | user1@gamil.com
69b10eea063e14aa724f7445 | user2  | user2@gmail.com
```

---

### Find Users with Filter

**Request:** "Find users older than 21"

**Response:**
```json
{
    "status": "success",
    "message": "Retrieved 5 document(s).",
    "valid": true,
    "mongodb_query": "db.users.find({ age: { $gt: 21 } }).limit(100)",
    "query": {
        "collection": "users",
        "operation": "find",
        "filter": {
            "age": {
                "$gt": 21
            }
        },
        "limit": 100
    },
    "data": {
        "columns": ["_id", "name", "age"],
        "rows": [...],
        "row_count": 5
    }
}
```

**UI Display:**
```
Generated MongoDB Query:
db.users.find({ age: { $gt: 21 } }).limit(100)

Results: 5 row(s)
[table with results]
```

---

### Count Documents

**Request:** "Count users older than 18"

**Response:**
```json
{
    "status": "success",
    "message": "Found 157 document(s).",
    "valid": true,
    "mongodb_query": "db.users.countDocuments({ age: { $gt: 18 } })",
    "query": {
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

**UI Display:**
```
Generated MongoDB Query:
db.users.countDocuments({ age: { $gt: 18 } })

Result: 157 documents found
```

---

### Aggregation Query

**Request:** "Get total sales per customer"

**Response:**
```json
{
    "status": "success",
    "message": "Retrieved 128 document(s).",
    "valid": true,
    "mongodb_query": "db.orders.aggregate([ { $match: { status: \"completed\" } }, { $group: { _id: \"$customer_id\", total: { $sum: \"$amount\" } } } ])",
    "query": {
        "collection": "orders",
        "operation": "aggregate",
        "pipeline": [
            {
                "$match": {
                    "status": "completed"
                }
            },
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
        "rows": [...],
        "row_count": 128
    }
}
```

**UI Display:**
```
Generated MongoDB Query:
db.orders.aggregate([ 
    { $match: { status: "completed" } }, 
    { $group: { _id: "$customer_id", total: { $sum: "$amount" } } } 
])

Results: 128 document(s)
[table with results]
```

---

### Distinct Query

**Request:** "Get all unique categories"

**Response:**
```json
{
    "status": "success",
    "message": "Found 12 unique value(s).",
    "valid": true,
    "mongodb_query": "db.products.distinct(\"category\", {})",
    "query": {
        "collection": "products",
        "operation": "distinct",
        "field": "category",
        "filter": {}
    },
    "data": {
        "columns": ["value"],
        "rows": [
            { "value": "Electronics" },
            { "value": "Clothing" },
            { "value": "Books" },
            ...
        ],
        "row_count": 12
    }
}
```

**UI Display:**
```
Generated MongoDB Query:
db.products.distinct("category", {})

Results: 12 unique values
- Electronics
- Clothing
- Books
...
```

---

### Error Response

**Request:** "List collections" (unsupported)

**Response:**
```json
{
    "status": "error",
    "message": "Error executing query: Query is not supported by the system",
    "valid": false,
    "retry_count": 2,
    "mongodb_query": null,
    "query": {
        "operation": "UNSUPPORTED_QUERY"
    }
}
```

**UI Display:**
```
Error: Query is not supported by the system
(Retries: 2)
```

---

## Generated MongoDB Query Formats

### Find Queries
```javascript
db.collection.find({})
db.collection.find({ age: { $gt: 18 } })
db.collection.find({}, { name: 1, email: 1 })
db.collection.find({}).sort({ age: -1 })
db.collection.find({}).skip(10).limit(100)
```

### Count Queries
```javascript
db.collection.countDocuments({})
db.collection.countDocuments({ status: "active" })
```

### Distinct Queries
```javascript
db.collection.distinct("field", {})
db.collection.distinct("category", { price: { $gt: 100 } })
```

### Aggregation Queries
```javascript
db.collection.aggregate([ 
    { $match: { status: "completed" } },
    { $group: { _id: "$customer_id", total: { $sum: "$amount" } } },
    { $sort: { total: -1 } }
])
```

---

## UI Implementation Examples

### React Component

```jsx
function QueryResults({ response }) {
  if (response.status === 'error') {
    return (
      <div className="error">
        <p>{response.message}</p>
        {response.mongodb_query && (
          <code>{response.mongodb_query}</code>
        )}
      </div>
    );
  }

  return (
    <div className="results">
      <h3>Generated MongoDB Query:</h3>
      <code className="mongodb-query">
        {response.mongodb_query}
      </code>
      
      <h3>Results: {response.data.row_count} row(s)</h3>
      <table>
        <thead>
          <tr>
            {response.data.columns.map(col => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {response.data.rows.map((row, idx) => (
            <tr key={idx}>
              {response.data.columns.map(col => (
                <td key={col}>{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### JavaScript/HTML

```html
<div class="query-result">
  <h3>Generated MongoDB Query:</h3>
  <code id="mongodb-query"></code>
  
  <div id="results-container"></div>
</div>

<script>
const response = fetch('/api/query').then(r => r.json());

response.then(data => {
  // Display MongoDB Query
  document.getElementById('mongodb-query').textContent = 
    data.response.mongodb_query;
  
  // Display Results
  if (data.response.status === 'success') {
    displayTable(data.response.data);
  } else {
    displayError(data.response.message);
  }
});
</script>
```

---

## Copy-Paste for Users

Users can directly copy the `mongodb_query` field and paste it into MongoDB shell:

```
User sees: db.users.find({}).limit(100)
User copies and pastes into MongoDB shell → Instant execution
```

---

## Benefits

✅ **No More JSON** - Users see MongoDB shell syntax they recognize  
✅ **Copy-Paste Ready** - Direct execution in MongoDB shell  
✅ **Audit Trail** - Track what queries were generated  
✅ **Education** - Shows users how to write MongoDB queries  
✅ **Debugging** - Easy to verify what query was executed  

---

## Response Field Summary

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| `status` | string | "success" | Query result status |
| `message` | string | "Retrieved 3 documents" | User-friendly message |
| `valid` | boolean | true | Whether query was valid |
| `mongodb_query` | string | "db.users.find({})" | **Executable MongoDB query** |
| `query` | object | {...} | Original JSON structure |
| `data` | object | {columns, rows} | Query results |
| `retry_count` | number | 2 | Retries on error |

---

This format provides both **human-readable MongoDB syntax** and **structured data** for UI display! 🎉
