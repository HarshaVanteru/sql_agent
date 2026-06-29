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
        # Include authSource=admin for authentication - most MongoDB setups authenticate against admin database
        mongo_url = f"mongodb://{encoded_user}:{encoded_password}@{host}:{port}/{database_name}?authSource=admin&serverSelectionTimeoutMS=5000&connectTimeoutMS=5000"
        logger.debug(f"MongoDB connection URL: mongodb://{username}:***@{host}:{port}/{database_name}?authSource=admin")
        client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        # Verify connection by running a simple command
        client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB at {host}:{port}")
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
        query = query.strip()

        # Handle listCollections metadata query
        if "listCollections" in query:
            collections = db.list_collection_names()
            logger.info(f"Listed {len(collections)} collections")
            return {
                "columns": ["collection_name"],
                "rows": [{"collection_name": name} for name in collections],
                "row_count": len(collections),
            }

        # Handle MongoDB shell syntax: db.collection.method(args)
        if query.startswith("db."):
            import re
            match = re.match(r'db\.(\w+)\.(\w+)\((.*)\)', query)
            if not match:
                raise ValueError(f"Invalid MongoDB shell syntax: {query}")

            collection_name = match.group(1)
            method = match.group(2)
            args_str = match.group(3)

            logger.info(f"Executing MongoDB {method} on collection: {collection_name}")
            collection = db[collection_name]

            if method == "find":
                query_filter = json.loads(args_str) if args_str else {}
                cursor = collection.find(query_filter).limit(100)
                rows = list(cursor)

            elif method == "countDocuments":
                query_filter = json.loads(args_str) if args_str else {}
                count = collection.count_documents(query_filter)
                rows = [{"count": count}]

            else:
                raise ValueError(f"Unsupported MongoDB method: {method}")

        else:
            # Legacy format: collection_name on first line, optional filter JSON on second line
            query_parts = query.split('\n', 1)
            collection_name = query_parts[0].strip()
            query_filter = {}

            if len(query_parts) > 1:
                try:
                    query_filter = json.loads(query_parts[1])
                except json.JSONDecodeError:
                    query_filter = {}

            logger.info(f"Executing MongoDB find on collection: {collection_name}")
            collection = db[collection_name]
            cursor = collection.find(query_filter).limit(100)
            rows = list(cursor)

        # Convert ObjectId to string for JSON serialization
        from bson import ObjectId
        for row in rows:
            if '_id' in row and isinstance(row['_id'], ObjectId):
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
