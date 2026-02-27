import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')
client = MongoClient(uri)
db = client['rigmaster']
col = db['components']

def find_duplicates():
    print("🔍 Checking for duplicates in 'components' collection...")
    
    pipeline = [
        {
            "$group": {
                "_id": {"name": "$name", "category": "$category"},
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}
            }
        }
    ]
    
    duplicates = list(col.aggregate(pipeline))
    print(f"Total groups of duplicate components: {len(duplicates)}")
    
    total_dupes_to_remove = sum(d['count'] - 1 for d in duplicates)
    print(f"Total extra instances to remove: {total_dupes_to_remove}")
    
    if total_dupes_to_remove > 0:
        print("🧹 Cleaning up duplicates...")
        to_delete = []
        for d in duplicates:
            # Keep the first ID, delete the rest
            to_delete.extend(d['ids'][1:])
        
        # Delete in batches to avoid large request issues
        batch_size = 1000
        deleted_count = 0
        for i in range(0, len(to_delete), batch_size):
            batch = to_delete[i:i + batch_size]
            result = col.delete_many({"_id": {"$in": batch}})
            deleted_count += result.deleted_count
            print(f"🚀 Removed {deleted_count}/{total_dupes_to_remove} duplicates...")

    print(f"\n✅ CLEANUP COMPLETE!")
    print(f"📊 Final Count in Atlas: {col.count_documents({})}")

    print("\n📌 Creating unique index to prevent future duplicates...")
    try:
        col.create_index([("name", 1), ("category", 1)], unique=True)
        print("✅ Unique index created successfully!")
    except Exception as e:
        print(f"⚠️ Could not create unique index (might still have data conflicts): {e}")

if __name__ == "__main__":
    find_duplicates()
