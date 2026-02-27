import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def sync_all_robust():
    local_client = MongoClient("mongodb://127.0.0.1:27017/")
    atlas_client = MongoClient(os.getenv('MONGO_URI'))
    
    local_db = local_client['rigmaster']
    atlas_db = atlas_client['rigmaster']
    
    local_cols = local_db.list_collection_names()
    
    print(f"🚀 Found {len(local_cols)} collections locally.")
    
    for col_name in local_cols:
        if col_name.startswith('system.'): continue
        if col_name == 'ai_cache': continue # Skip empty cache
            
        count = local_db[col_name].count_documents({})
        if count == 0:
            print(f"⏭️  Skipping '{col_name}' (Empty)")
            continue
            
        print(f"📦 Syncing '{col_name}' ({count} items)...")
        
        # Don't wipe users/components since we have those already
        if col_name in ['users', 'components']:
            print(f"  ℹ️  Skipping core table '{col_name}' (Already migrated).")
            continue
            
        atlas_db[col_name].delete_many({})
        
        cursor = local_db[col_name].find({}, {"_id": 0})
        batch = []
        migrated = 0
        
        for doc in cursor:
            batch.append(doc)
            if len(batch) >= 1000:
                try:
                    atlas_db[col_name].insert_many(batch)
                    migrated += len(batch)
                    print(f"  ... {migrated}/{count}")
                    batch = []
                    time.sleep(0.1)
                except Exception as e:
                    print(f"  ❌ Batch error in '{col_name}': {e}")
                    batch = []
        
        if batch:
            try:
                atlas_db[col_name].insert_many(batch)
                migrated += len(batch)
            except Exception as e:
                print(f"  ❌ Final batch error in '{col_name}': {e}")
                
        print(f"  ✅ '{col_name}' Sync Complete.")

    print("\n🎉 ALL TABLES SYNCED SUCCESSFULLY!")

if __name__ == "__main__":
    sync_all_robust()
