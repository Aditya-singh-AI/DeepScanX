import os
from pymongo import MongoClient

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['aura_db']

target_email = "aditya.asb24@gmail.com"

# Find the admin document
admin_doc = db.users.find_one({"email": target_email, "role": "admin"})

if not admin_doc:
    print(f"Could not find admin document with email {target_email}!")
else:
    print(f"Admin doc found: {admin_doc['_id']}")
    
    # Let's find any documents that ONLY have a supabase_id but NO email
    # This might have been created by mistake
    bad_docs = list(db.users.find({
        "email": {"$in": [None, ""]}, 
        "supabase_id": {"$exists": True}
    }))
    
    for bad in bad_docs:
        print(f"Removing empty patient record created by mistake: {bad['_id']} -> {bad.get('supabase_id')}")
        db.users.delete_one({"_id": bad["_id"]})

print("Cleanup complete.")
