import os
import json
from pymongo import MongoClient

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['aura_db']

users = list(db.users.find())
output = []
for u in users:
    output.append({
        "id": str(u.get("_id")),
        "email": u.get("email"),
        "role": u.get("role"),
        "supabase_id": u.get("supabase_id") or u.get("clerk_id")
    })

print(json.dumps(output, indent=2))
