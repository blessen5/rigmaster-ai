from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
collections = db.list_collection_names()
with open('all_counts.txt', 'w') as f:
    for col in collections:
        count = db[col].count_documents({})
        f.write(f"{col}: {count}\n")
