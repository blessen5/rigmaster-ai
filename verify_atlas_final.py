import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
c = MongoClient(os.getenv('MONGO_URI'))
db = c['rigmaster']
cols = db.list_collection_names()
print("--- ATLAS STATUS ---")
for col in sorted(cols):
    count = db[col].count_documents({})
    print(f"{col}: {count}")
