from app2.models import db
import sys

def make_admin(email):
    res = db.users.update_one({"email": email}, {"$set": {"role": "admin"}})
    if res.matched_count > 0:
        print(f"Successfully made {email} an admin!")
    else:
        print(f"User {email} not found. Please sign up first.")

if __name__ == '__main__':
    make_admin('aditya.asb24@gmail.com')
