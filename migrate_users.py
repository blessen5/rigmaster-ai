import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def migrate_users():
    local_client = MongoClient("mongodb://127.0.0.1:27017/")
    atlas_client = MongoClient(os.getenv('MONGO_URI'))
    
    local_db = local_client['rigmaster']
    atlas_db = atlas_client['rigmaster']
    
    count = local_db.users.count_documents({})
    print(f"Found {count} users locally.")
    
    if count > 0:
        print("Migrating users to Atlas...")
        users = list(local_db.users.find())
        for user in users:
            # Check if user already exists based on username
            if not atlas_db.users.find_one({"username": user["username"]}):
                atlas_db.users.insert_one(user)
                print(f"✅ Migrated: {user['username']}")
            else:
                print(f"⏭️  Already exists: {user['username']}")
    
    print("\n🎉 Migration check complete. You can now login using your local credentials!")

if __name__ == "__main__":
    migrate_users()
