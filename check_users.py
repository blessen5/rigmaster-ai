from pymongo import MongoClient
import os

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    users = list(db.users.find({}, {'password': 0})) # Don't log passwords
    with open('users_check.txt', 'w') as f:
        f.write(f"Users count: {len(users)}\n")
        for u in users:
            f.write(f"User: {u}\n")
except Exception as e:
    with open('users_check.txt', 'w') as f:
        f.write(f"Error: {e}")
