from pymongo import MongoClient
import os
import sys

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    db = client['rigmaster']
    
    user = db.users.find_one()
    if user:
        print(f"User: {user['username']} ({user['_id']})")
        # Try both ObjectId and string for user_id
        builds = list(db.saved_builds.find({
            '$or': [
                {'user_id': user['_id']},
                {'user_id': str(user['_id'])}
            ]
        }))
        
        if not builds:
            print("No builds found for this user. Listing all builds:")
            builds = list(db.saved_builds.find().limit(5))
            
        for b in builds:
            print(f"Build ID: {b['_id']} - Name: {b.get('name')}")
    else:
        print("No users found")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
