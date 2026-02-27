from pymongo import MongoClient
import os

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
with open('db_report.txt', 'w') as f:
    f.write(f"Collections: {db.list_collection_names()}\n")
    for col in ['cpus', 'gpus', 'motherboards']:
        if col in db.list_collection_names():
            f.write(f"{col} count: {db[col].count_documents({})}\n")
            doc = db[col].find_one()
            f.write(f"{col} sample doc: {doc}\n")
