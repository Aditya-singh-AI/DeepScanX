import os
from pymongo import MongoClient

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['aura_db']

email = "aditya.asb24@gmail.com"

# Find any user with this email and update their role
result = db.users.update_many(
    {"email": email},
    {"$set": {"role": "admin"}}
)

print(f"Matched {result.matched_count} users by email.")
print(f"Modified {result.modified_count} users to have role 'admin'.")
