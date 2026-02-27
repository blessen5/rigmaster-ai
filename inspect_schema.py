from pymongo import MongoClient
import json
from bson import ObjectId

def default_serializer(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return str(obj)

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

collections = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']
sample_data = {}

for col in collections:
    doc = db[col].find_one()
    if doc:
        # Simplify for display
        filtered = {k: v for k, v in doc.items() if k in ['name', 'price', 'brand', 'socket', 'memory_type', 'wattage', 'chipset', 'capacity']}
        sample_data[col] = filtered

with open('schema_sample.txt', 'w') as f:
    f.write(json.dumps(sample_data, default=default_serializer, indent=2))
