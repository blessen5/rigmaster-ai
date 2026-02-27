import os
import sys
import time
from pymongo import MongoClient
from dotenv import load_dotenv

def log(msg):
    print(msg)
    with open('migration_v2.log', 'a', encoding='utf-8') as f:
        f.write(str(msg) + "\n")

def run():
    load_dotenv()
    if os.path.exists('migration_v2.log'): os.remove('migration_v2.log')
    
    local_uri = "mongodb://127.0.0.1:27017/"
    atlas_uri = os.getenv('MONGO_URI')
    
    log(f"Starting Migration v2")
    log(f"Local: {local_uri}")
    log(f"Atlas Cluster: {atlas_uri.split('@')[1] if '@' in atlas_uri else 'N/A'}")

    try:
        local_client = MongoClient(local_uri, serverSelectionTimeoutMS=5000)
        atlas_client = MongoClient(atlas_uri, serverSelectionTimeoutMS=10000)
        
        local_db = local_client['rigmaster']
        atlas_db = atlas_client['rigmaster']
        
        total_count = local_db.components.count_documents({})
        log(f"Items to migrate: {total_count}")
        
        if total_count == 0:
            log("❌ No items found in local 'components' collection.")
            return

        cursor = local_db.components.find({}, {"_id": 0})
        batch = []
        migrated = 0
        
        for doc in cursor:
            batch.append(doc)
            if len(batch) >= 1000:
                atlas_db.components.insert_many(batch, ordered=False)
                migrated += len(batch)
                log(f"✅ Migrated {migrated}/{total_count}")
                batch = []
                time.sleep(0.5)
        
        if batch:
            atlas_db.components.insert_many(batch, ordered=False)
            migrated += len(batch)
            log(f"✅ Final Migration Complete: {migrated} items.")

    except Exception as e:
        log(f"❌ FATAL ERROR: {e}")

if __name__ == "__main__":
    run()
