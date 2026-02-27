import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
LOCAL_URI = "mongodb://127.0.0.1:27017/"
ATLAS_URI = os.getenv('MONGO_URI')
DATABASE_NAME = "rigmaster"
COLLECTION_NAME = "components"
BATCH_SIZE = 500  # Smaller batches for Atlas stability

def log(msg):
    print(msg)
    with open('migration_progress.log', 'a') as f:
        f.write(str(msg) + "\n")

def migrate():
    if os.path.exists('migration_progress.log'): os.remove('migration_progress.log')
    log("🛸 Starting Migration to MongoDB Atlas...")
    
    # Connect to Local
    try:
        local_client = MongoClient(LOCAL_URI)
        local_db = local_client[DATABASE_NAME]
        local_col = local_db[COLLECTION_NAME]
        total_local = local_col.count_documents({})
        log(f"📍 Local database found. Total components: {total_local}")
    except Exception as e:
        log(f"❌ Error connecting to local DB: {e}")
        return

    # Connect to Atlas
    try:
        atlas_client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000)
        atlas_db = atlas_client[DATABASE_NAME]
        atlas_col = atlas_db[COLLECTION_NAME]
        # Test connection
        atlas_client.admin.command('ping')
        log("🌌 Connected to MongoDB Atlas!")
    except Exception as e:
        log(f"❌ Error connecting to Atlas: {e}")
        return

    # Start Migration
    log(f"🔥 Migrating {total_local} items in batches of {BATCH_SIZE}...")
    
    cursor = local_col.find({}, {"_id": 0}) # Exclude _id to let Atlas generate new ones
    batch = []
    count = 0
    total_migrated = 0

    for item in cursor:
        batch.append(item)
        count += 1
        
        if len(batch) >= BATCH_SIZE:
            try:
                atlas_col.insert_many(batch, ordered=False)
                total_migrated += len(batch)
                log(f"🚀 Progress: {total_migrated}/{total_local} items uploaded...")
                batch = []
                time.sleep(0.1) # Brief pause to avoid rate limiting on free tier
            except Exception as e:
                log(f"⚠️ Batch error (skipping duplicates): {e}")
                batch = []

    # Insert remaining
    if batch:
        try:
            atlas_col.insert_many(batch, ordered=False)
            total_migrated += len(batch)
        except Exception as e:
            print(f"⚠️ Final batch error: {e}")

    print(f"\n✅ SUCCESS! Migrated {total_migrated} components to Atlas.")
    print(f"📊 Final Check: Atlas now has {atlas_col.count_documents({})} components.")

if __name__ == "__main__":
    migrate()
