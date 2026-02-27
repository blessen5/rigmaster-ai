import requests
import json
from pymongo import MongoClient

# Get a real component ID from the database
client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

# Get one component from each category
cpu = db.components.find_one({'category': 'cpu'})
mobo = db.components.find_one({'category': 'motherboard'})
ram = db.components.find_one({'category': 'ram'})

print("=== Testing Blueprint API with Real Data ===\n")

if cpu and mobo and ram:
    print(f"CPU: {cpu['name']} (ID: {cpu['_id']})")
    print(f"Motherboard: {mobo['name']} (ID: {mobo['_id']})")
    print(f"RAM: {ram['name']} (ID: {ram['_id']})")
    print()
    
    # Test the API
    url = "http://localhost:5001/api/build-blueprint"
    data = {
        "cpu_id": str(cpu['_id']),
        "motherboard_id": str(mobo['_id']),
        "ram_id": str(ram['_id']),
        "gpu_id": None,
        "storage_id": None,
        "psu_id": None,
        "case_id": None,
        "cooler_id": None
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")
else:
    print("ERROR: Could not find components in database")
    print(f"CPU found: {cpu is not None}")
    print(f"Motherboard found: {mobo is not None}")
    print(f"RAM found: {ram is not None}")
