"""
Run this script ONCE via Railway Shell or local terminal to reset admin password.
Usage: python reset_admin.py
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

load_dotenv()

ADMIN_EMAIL = "admin@rigmaster.com"
ADMIN_PASSWORD = "Admin@1234"  # Change this to your preferred password
ADMIN_USERNAME = "admin"

def reset_admin():
    uri = os.getenv('MONGO_URI')
    if not uri:
        print("ERROR: MONGO_URI not set")
        return
        
    print(f"Connecting to MongoDB...")
    c = MongoClient(uri, serverSelectionTimeoutMS=10000)
    c.admin.command('ping')
    print("Connected!")
    
    db = c['rigmaster']
    
    # Check current users
    users = list(db.users.find({}, {'password': 0}))
    print(f"\nCurrent users in Atlas: {len(users)}")
    for u in users:
        print(f"  - {u.get('email', 'no email')} | admin={u.get('is_admin', False)}")
    
    # Update or create admin user
    new_hash = generate_password_hash(ADMIN_PASSWORD)
    result = db.users.update_one(
        {'email': ADMIN_EMAIL},
        {'$set': {
            'email': ADMIN_EMAIL,
            'username': ADMIN_USERNAME,
            'password': new_hash,
            'is_admin': True,
            'name': 'Admin'
        }},
        upsert=True
    )
    
    if result.upserted_id:
        print(f"\n✅ Created new admin user!")
    else:
        print(f"\n✅ Updated existing admin user password!")
    
    print(f"\nAdmin Credentials:")
    print(f"  Email: {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")

if __name__ == "__main__":
    reset_admin()
