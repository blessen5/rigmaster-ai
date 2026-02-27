from pymongo import MongoClient
import json

def list_keys():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    keys = [doc['cache_key'] for doc in db.ai_cache.find({}, {"cache_key": 1})]
    print(f"Total keys: {len(keys)}")
    for k in keys:
        print(f"Key: {k}")

if __name__ == "__main__":
    list_keys()
