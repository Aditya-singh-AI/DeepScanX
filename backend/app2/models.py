from pymongo import MongoClient
import os
from bson.objectid import ObjectId

# Initialize MongoDB Client - MUST use MONGO_URI from environment
# On Render: set MONGO_URI to MongoDB Atlas connection string
# e.g., mongodb+srv://user:pass@cluster.mongodb.net/aura_db?retryWrites=true&w=majority
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    # Force a connection check — this will throw immediately if misconfigured
    client.server_info()
    print(f"[DB] Connected to MongoDB: {mongo_uri[:40]}...")
except Exception as e:
    import sys
    print(f"[DB] FATAL: Cannot connect to MongoDB. URI: {mongo_uri[:40]}... Error: {e}", file=sys.stderr)
    # Don't crash the app at import time — let individual routes fail gracefully
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

db = client['aura_db']

# Helper function to convert string IDs to ObjectId
def get_object_id(id_str):
    try:
        return ObjectId(id_str)
    except:
        return None