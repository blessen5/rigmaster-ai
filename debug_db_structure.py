from pymongo import MongoClient
import json

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['rigmaster']

stats = {}
for cat in ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler']:
    count = db.components.count_documents({'category': cat})
    sample = list(db.components.find({'category': cat}).limit(1))
    if sample:
        sample = sample[0]
        sample['_id'] = str(sample['_id'])
    stats[cat] = {
        'count': count,
        'sample_keys': list(sample.keys()) if sample else None,
        'has_name': 'name' in sample if sample else False
    }

print(json.dumps(stats, indent=2))
