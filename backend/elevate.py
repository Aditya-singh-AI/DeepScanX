import os
from pymongo import MongoClient

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['aura_db']

target_email = "aditya.asb24@gmail.com"

# 1. Update the original email record
db.users.update_many({"email": target_email}, {"$set": {"role": "admin"}})

print("Admin privileges applied successfully to MongoDB.")
