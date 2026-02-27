
from pymongo import MongoClient
import json

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
sample = db.group_builds.find_one()
if sample:
    sample['_id'] = str(sample['_id'])
    print(json.dumps(sample, indent=2))
else:
    print("No group builds found")
