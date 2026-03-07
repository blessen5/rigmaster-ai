
import requests
import json

base_url = "http://127.0.0.1:5005"

# We need some real IDs from the database to test
# I'll just use the check_unified_counts.py results but I need actual ObjectIds
# Wait, I'll just write a script that fetches the first item from each category and then calls api_component_prices

from pymongo import MongoClient
import os
from bson.objectid import ObjectId

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['rigmaster']

test_data = {}
categories = ['monitor', 'os', 'peripherals', 'fans']

for cat in categories:
    item = db.components.find_one({'category': cat})
    if item:
        test_data[cat + '_id'] = str(item['_id'])
        print(f"Found {cat}: {item.get('name')} ({item['_id']})")

if not test_data:
    print("No test data found!")
    exit()

# Add basic components to satisfy any checks
cpu = db.components.find_one({'category': 'cpu'})
if cpu: test_data['cpu_id'] = str(cpu['_id'])

try:
    response = requests.post(f"{base_url}/api/component-prices", json=test_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error calling API: {e}")
