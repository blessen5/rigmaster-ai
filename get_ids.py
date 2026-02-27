from pymongo import MongoClient
import json

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['rigmaster']
cols = ['cpus', 'motherboards', 'ram', 'gpus', 'storage', 'psu']
results = {}

for c in cols:
    doc = db[c].find_one()
    if doc:
        results[c] = str(doc['_id'])

print(json.dumps(results))
