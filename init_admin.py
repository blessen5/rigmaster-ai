from pymongo import MongoClient
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

def init_admin():
    uri = 'mongodb://localhost:27017/'
    client = MongoClient(uri)
    db = client['rigmaster']
    
    # Check if admin already exists
    admin = db.users.find_one({'username': 'admin'})
    if admin:
        print("Admin user already exists. Promoting to admin status...")
        db.users.update_one({'_id': admin['_id']}, {'$set': {'is_admin': True, 'is_active': True}})
        return

    print("Creating default admin user...")
    hashed_password = generate_password_hash('admin123')
    db.users.insert_one({
        'username': 'admin',
        'email': 'admin@rigmaster.ai',
        'password': hashed_password,
        'is_admin': True,
        'is_active': True,
        'created_at': datetime.now(timezone.utc)
    })
    print("Admin user created: admin / admin123")

if __name__ == "__main__":
    init_admin()
