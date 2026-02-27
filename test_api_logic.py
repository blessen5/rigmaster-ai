from pymongo import MongoClient
import json
import os

MONGO_URI = 'mongodb://localhost:27017/'
client = MongoClient(MONGO_URI)
db = client['rigmaster']

def get_component_list(category_name):
    cat_map = {
        'cpus': 'cpu',
        'gpus': 'gpu',
        'motherboards': 'motherboard',
        'ram': 'ram',
        'storage': 'storage',
        'psu': 'psu',
        'cases': 'case',
        'coolers': 'cooler'
    }
    target_cat = cat_map.get(category_name, category_name)
    print(f"Fetching {category_name} (mapped to {target_cat})...")
    
    items = list(db.components.find({'category': target_cat}, {'name': 1, 'status': 1, 'brand': 1}).sort('name', 1))
    print(f"Found {len(items)} items.")
    
    return [{
        'id': str(item['_id']), 
        'name': item.get('name', 'Unknown'),
        'status': item.get('status', 'Active'),
        'brand': item.get('brand', 'Unknown')
    } for item in items]

for cat in ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']:
    try:
        results = get_component_list(cat)
        print(f"Successfully processed {cat} list logic.")
    except Exception as e:
        print(f"FAILED {cat}: {e}")
