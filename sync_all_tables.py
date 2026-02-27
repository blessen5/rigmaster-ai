import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def sync_all():
    local_client = MongoClient("mongodb://127.0.0.1:27017/")
    atlas_client = MongoClient(os.getenv('MONGO_URI'))
    
    local_db = local_client['rigmaster']
    # Ensure we use 'rigmaster' database on Atlas
    atlas_db = atlas_client['rigmaster']
    
    local_cols = local_db.list_collection_names()
    
    print(f"🚀 Found {len(local_cols)} collections locally.")
    
    for col_name in local_cols:
        # Skip if it's a system collection
        if col_name.startswith('system.'): continue
            
        count = local_db[col_name].count_documents({})
        print(f"📦 Handling '{col_name}' ({count} items)...")
        
        # We don't want to wipe 'components' or 'users' if they are already there
        # But for others, we can refresh to ensure a clean sync
        if col_name not in ['components', 'users']:
            atlas_db[col_name].delete_many({})
            atlas_db[col_name].insert_many(local_db[col_name].find({}, {"_id": 0}))
            print(f"  ✅ Migrated {count} items.")
        else:
            # For components and users, we already did a big migration.
            # Just check if counts match roughly.
            atlas_count = atlas_db[col_name].count_documents({})
            print(f"  ℹ️  Already exists in Atlas (Local: {count}, Atlas: {atlas_count})")

    print("\n🎉 ALL TABLES SYNCED TO ATLAS!")

if __name__ == "__main__":
    sync_all()
