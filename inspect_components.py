
from pymongo import MongoClient
import os
import json
from bson.objectid import ObjectId

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['rigmaster']

output = []
categories = ['monitor', 'os', 'peripherals', 'fans']
for cat in categories:
    item = db.components.find_one({'category': cat})
    if item:
        item['_id'] = str(item['_id'])
        output.append(f"CATEGORY: {cat}")
        output.append(json.dumps(item, indent=2))
        output.append("-" * 20)
    else:
        output.append(f"CATEGORY: {cat} - NO ITEM FOUND")

with open('inspection_results.txt', 'w') as f:
    f.write("\n".join(output))
