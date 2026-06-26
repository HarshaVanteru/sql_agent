"""MongoDB database connection and query execution."""
import json
import logging
from urllib.parse import quote_plus
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("pymongo not available - MongoDB queries will be disabled")


def create_mongodb_connection(host: str, port: int, username: str, password: str, database_name: str):
    """Create a MongoDB client connection."""
    if not MONGODB_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "MONGODB_NOT_AVAILABLE", "message": "MongoDB driver is not installed"},
        )

    try:
        encoded_user = quote_plus(username)
        encoded_password = quote_plus(password)
        mongo_url = f"mongodb://{encoded_user}:{encoded_password}@{host}:{port}/{database_name}"
        logger.debug(f"MongoDB connection URL: mongodb://{username}:***@{host}:{port}/{database_name}")
        client = pymongo.MongoClient(mongo_url)
        return client
    except Exception as e:
        logger.error(f"Failed to create MongoDB connection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONNECTION_ERROR", "message": f"Failed to connect to MongoDB: {str(e)}"},
        )


def execute_mongodb_query(client, database_name: str, query: str) -> dict:
    """Execute a query against MongoDB database."""
    if not MONGODB_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "MONGODB_NOT_AVAILABLE", "message": "MongoDB driver is not installed"},
        )

    try:
        db = client[database_name]

        # Parse MongoDB query - expect collection name and query JSON
        query_parts = query.strip().split('\n', 1)
        collection_name = query_parts[0].strip()
        query_filter = {}

        if len(query_parts) > 1:
            try:
                query_filter = json.loads(query_parts[1])
            except json.JSONDecodeError:
                query_filter = {}

        logger.info(f"Executing MongoDB query on collection: {collection_name}")
        collection = db[collection_name]
        cursor = collection.find(query_filter)
        rows = list(cursor)

        # Convert ObjectId to string for JSON serialization
        for row in rows:
            if '_id' in row:
                row['_id'] = str(row['_id'])

        columns = list(rows[0].keys()) if rows else []

        logger.info(f"MongoDB query executed successfully - returned {len(rows)} rows")
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }
    except Exception as e:
        logger.error(f"MongoDB query execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "QUERY_ERROR", "message": f"Query execution failed: {str(e)}"},
        )
    finally:
        if client:
            client.close()


def get_mongodb_schema(client, database_name: str) -> str:
    """Fetch schema from MongoDB database."""
    if not MONGODB_AVAILABLE:
        return "MongoDB driver not available"

    try:
        db = client[database_name]
        collections = db.list_collection_names()

        schema_str = "MongoDB Collections:\n"
        for collection_name in collections:
            collection = db[collection_name]
            sample_doc = collection.find_one()
            if sample_doc:
                fields = list(sample_doc.keys())
                schema_str += f"\nCollection: {collection_name}\n"
                schema_str += "  Fields:\n"
                for field in fields:
                    schema_str += f"    - {field}\n"

        return schema_str

    except Exception as e:
        logger.error(f"Failed to fetch MongoDB schema: {str(e)}", exc_info=True)
        return "Failed to fetch MongoDB schema"
