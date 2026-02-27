from pymongo import MongoClient
import json

def check():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    cache = db.ai_cache.find_one({"cache_key": {"$regex": "^resale_v4_"}})
    if cache:
        with open('cache_inspect.json', 'w') as f:
            json.dump(cache['prediction'], f, indent=2)
        print("Found cache")
    else:
        print("No cache found")

if __name__ == "__main__":
    check()
