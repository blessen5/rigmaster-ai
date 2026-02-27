import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017/')
client = MongoClient(MONGO_URI)
db = client['rigmaster']

def verify_data():
    print("--- Database Audit ---")
    
    # 1. Check counts in 'components'
    total_components = db.components.count_documents({})
    print(f"Total documents in 'components': {total_components}")
    
    # 2. Check categories
    categories = db.components.distinct('category')
    print(f"Categories found: {categories}")
    
    # 3. Check for ANY document with a brand
    branded = db.components.find_one({'brand': {'$exists': True, '$ne': None, '$ne': ""}})
    if branded:
        print(f"Foud branded item: {branded.get('name')} | Brand: {branded.get('brand')}")
    else:
        print("ALERT: No branded items found in 'components' collection.")
        
    # 4. Check other collections (if data was imported there by mistake)
    other_cols = [c for c in db.list_collection_names() if c not in ['components', 'users', 'saved_builds', 'ai_cache', 'shopping_cache', 'admin', 'config', 'local']]
    print(f"Other data collections: {other_cols}")
    for col in other_cols:
        count = db[col].count_documents({})
        if count > 0:
            sample = db[col].find_one()
            print(f"  Collection '{col}': {count} docs. Sample: {sample.get('name')} | Brand: {sample.get('brand')}")

    # 5. Spot check for 'Genunieness'
    # We'll look at a few common parts and see if their specs match reality
    print("\n--- Genuineness Spot Check ---")
    verified_refs = [
        {"name": "Intel Core i9-14900K", "socket": "LGA1700", "cores": 24},
        {"name": "NVIDIA GeForce RTX 4090", "vram": "24GB", "tdp": "450W"},
        {"name": "AMD Ryzen 7 7800X3D", "socket": "AM5", "cores": 8}
    ]
    
    for ref in verified_refs:
        doc = db.components.find_one({"name": {"$regex": ref['name'], "$options": "i"}})
        if doc:
            print(f"Checking {ref['name']}:")
            for key, expected in ref.items():
                if key == 'name': continue
                actual = doc.get(key)
                match = "MATCH" if str(expected).lower() in str(actual).lower() else "MISMATCH"
                print(f"  {key}: Expected {expected}, Got {actual} -> {match}")
        else:
            print(f"Checking {ref['name']}: NOT FOUND in 'components'")

if __name__ == "__main__":
    verify_data()
