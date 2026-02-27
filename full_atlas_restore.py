import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def restore_full_database():
    local_client = MongoClient("mongodb://127.0.0.1:27017/")
    atlas_client = MongoClient(os.getenv('MONGO_URI'))
    
    local_db = local_client['rigmaster']
    atlas_db = atlas_client['rigmaster']
    
    local_col = local_db.components
    atlas_col = atlas_db.components
    
    print(f"Reading local database... Count: {local_col.count_documents({})}")
    
    print("Preparing Atlas collection...")
    # Drop unique index if it exists
    try:
        atlas_col.drop_index("name_1_category_1")
        print("✅ Unique index dropped.")
    except Exception as e:
        print(f"ℹ️ No unique index to drop or error: {e}")
        
    # Clear Atlas components (important to avoid mixing with previous half-done or deduplicated data)
    atlas_col.delete_many({})
    print("✅ Atlas collection cleared.")
    
    print("Starting full migration (preserving all listings)...")
    
    cursor = local_col.find({}, {"_id": 0})
    batch = []
    total_migrated = 0
    total_local = local_col.count_documents({})
    
    for doc in cursor:
        batch.append(doc)
        if len(batch) >= 1000:
            atlas_col.insert_many(batch)
            total_migrated += len(batch)
            print(f"🚀 Progress: {total_migrated}/{total_local}")
            batch = []
            time.sleep(0.5)
            
    if batch:
        atlas_col.insert_many(batch)
        total_migrated += len(batch)
        
    print(f"\n✨ SUCCESS! Final Atlas Count: {atlas_col.count_documents({})}")

if __name__ == "__main__":
    restore_full_database()
