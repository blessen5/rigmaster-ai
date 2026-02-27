import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def full_sync():
    local_client = MongoClient("mongodb://127.0.0.1:27017/")
    atlas_client = MongoClient(os.getenv('MONGO_URI'))
    
    local_db = local_client['rigmaster']
    atlas_db = atlas_client['rigmaster']
    
    # Collections we want to ensure are migrated
    collections = [
        'saved_builds', 'group_builds', 'group_projects', 
        'complaints', 'settings', 'shopping_cache',
        'cpus', 'gpus', 'motherboards', 'ram', 'storage', 
        'psu', 'cases', 'coolers'
    ]
    
    print("🚀 Starting Full Table Migration to Atlas...")
    
    for col_name in collections:
        count = local_db[col_name].count_documents({})
        if count == 0:
            print(f"⏭️  Skipping '{col_name}' (Empty)")
            continue
            
        print(f"📦 Migrating '{col_name}' ({count} items)...")
        
        # Clear existing in Atlas to avoid duplicates on re-run
        atlas_db[col_name].delete_many({})
        
        cursor = local_db[col_name].find({}, {"_id": 0})
        batch = []
        migrated = 0
        
        for doc in cursor:
            batch.append(doc)
            if len(batch) >= 500:
                atlas_db[col_name].insert_many(batch)
                migrated += len(batch)
                print(f"  ... {migrated}/{count}")
                batch = []
                time.sleep(0.2)
        
        if batch:
            atlas_db[col_name].insert_many(batch)
            migrated += len(batch)
            
        print(f"  ✅ Done: {migrated} items.")

    print("\n🎉 ALL TABLES MIGRATED SUCCESSFULLY!")

if __name__ == "__main__":
    full_sync()
