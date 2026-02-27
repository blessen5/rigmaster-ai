import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def sync_missing():
    local_client = MongoClient("mongodb://127.0.0.1:27017/")
    atlas_client = MongoClient(os.getenv('MONGO_URI'))
    
    local_db = local_client['rigmaster']
    atlas_db = atlas_client['rigmaster']
    
    local_col = local_db.components
    atlas_col = atlas_db.components
    
    print(f"Local Count: {local_col.count_documents({})}")
    print(f"Atlas Count: {atlas_col.count_documents({})}")
    
    print("Finding missing items...")
    
    # Get all names/categories from Atlas for fast lookup
    atlas_items = set()
    for item in atlas_col.find({}, {"name": 1, "category": 1}):
        atlas_items.add((item['name'], item['category']))
    
    missing = []
    for item in local_col.find({}, {"_id": 0}):
        if (item['name'], item['category']) not in atlas_items:
            missing.append(item)
    
    print(f"Detected {len(missing)} missing items.")
    
    if missing:
        print("Uploading missing items...")
        # Upload in batches
        for i in range(0, len(missing), 500):
            batch = missing[i:i+500]
            atlas_col.insert_many(batch)
            print(f"Uploaded {i+len(batch)} items...")
            
    print(f"Final Atlas Count: {atlas_col.count_documents({})}")

if __name__ == "__main__":
    sync_missing()
