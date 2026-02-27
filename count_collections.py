from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    collections = db.list_collection_names()
    with open('collections_count.txt', 'w') as f:
        f.write(f"Total collections (tables): {len(collections)}\n")
        f.write(f"Collections: {collections}\n")
except Exception as e:
    with open('collections_count.txt', 'w') as f:
        f.write(f"Error: {e}")
