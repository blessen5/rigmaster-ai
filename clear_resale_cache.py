from pymongo import MongoClient

def clear_resale_cache():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    res = db.ai_cache.delete_many({"cache_key": {"$regex": "^resale_"}})
    print(f"Cleared {res.deleted_count} resale cache entries.")

if __name__ == "__main__":
    clear_resale_cache()
