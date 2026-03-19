import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client.get_database()

categories = ['cpu', 'gpu', 'motherboard', 'ram', 'psu', 'case', 'cooler', 'monitor', 'ups', 'network_adapter']

for cat in categories:
    print(f"\n--- Category: {cat} ---")
    doc = db.components.find_one({'category': cat})
    if doc:
        for k, v in doc.items():
            print(f"{k}: {v}")
    else:
        print("No document found.")

client.close()
