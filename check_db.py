from pymongo import MongoClient
import json

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
collections = db.list_collection_names()
stats = {c: db[c].count_documents({}) for c in collections}

print(json.dumps(stats, indent=2))
