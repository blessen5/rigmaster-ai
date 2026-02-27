
from pymongo import MongoClient
import os

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['rigmaster']

categories = ['monitor', 'os', 'peripherals', 'fans']
results = {}

for cat in categories:
    count = db.components.count_documents({'category': cat})
    results[cat] = count

with open('components_unified_counts.txt', 'w') as f:
    for cat, count in results.items():
        f.write(f"{cat}: {count}\n")
