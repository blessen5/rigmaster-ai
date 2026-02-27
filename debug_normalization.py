
import os
import json
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId

def test_recommendation():
    # Setup mock request data
    data = {
        "budget": 1200,
        "usage": "gaming",
        "requirements": "RTX GPU",
        "provider": "gemini"
    }
    
    # We'll just call the logic directly if possible, or simulate it.
    # Since I can't easily call the Flask route in a script without a context,
    # I will just create a script that mimics the normalization logic to see if it's broken.
    
    # Mock database
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    
    # Mock result from AI
    result = {
        "build": {
            "CPU": "696999e41dce692221d00cd2", # Valid ID from my earlier check
            "GPU": "696999e51dce692221d01095"
        }
    }
    
    def get_estimated_price(comp_name, cat):
        return 100 # Mock

    # Normalization logic
    final_build = {}
    target_keys = ['CPU', 'GPU', 'Motherboard', 'RAM', 'Storage', 'PSU', 'Case', 'Cooler']
    col_map = {
        'CPU': 'cpus', 'GPU': 'gpus', 'Motherboard': 'motherboards',
        'RAM': 'ram', 'Storage': 'storage', 'PSU': 'psu',
        'Case': 'cases', 'Cooler': 'coolers'
    }
    
    raw_build = result.get('build', {})
    import re
    total_calculated_cost = 0
    
    for key in target_keys:
        val = None
        possible_keys = [key, key.lower(), key.upper(), key.lower() + 's', key.upper() + 's', key.replace('CPU', 'processor').lower(), key.replace('GPU', 'graphics').lower()]
        for pk in possible_keys:
            if pk in raw_build:
                val = raw_build[pk]
                break
        
        if not val:
            continue
            
        comp_id = None
        if isinstance(val, str):
            match = re.search(r'[0-9a-fA-F]{24}', val)
            if match:
                comp_id = match.group(0)
        
        if comp_id:
            try:
                col = col_map[key]
                comp = db[col].find_one({'_id': ObjectId(comp_id)})
                if comp:
                    price = comp.get('price') or comp.get('estimated_price')
                    if not price or price == '---' or price == 0:
                        price = get_estimated_price(comp.get('name'), col)
                    
                    final_build[key] = {
                        'id': str(comp['_id']),
                        'name': comp.get('name', 'Unknown'),
                        'estimated_price': f"{price}" if not str(price).startswith('$') else str(price)
                    }
                    print(f"Added {key}: {final_build[key]}")
            except Exception as ex:
                print(f"Error for {key}: {ex}")

    print("Final Build Keys:", final_build.keys())
    for k, v in final_build.items():
        print(f"{k}: {type(v)} - {v}")

if __name__ == "__main__":
    test_recommendation()
