from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

with open("ddr3_hunt.txt", "w") as f:
    try:
        client = MongoClient(uri)
        db = client['rigmaster']
        # Search for "DDR3" in any field of any component
        results = list(db.components.find({
            '$or': [
                {'name': {'$regex': 'DDR3', '$options': 'i'}},
                {'type': {'$regex': 'DDR3', '$options': 'i'}},
                {'ram_type': {'$regex': 'DDR3', '$options': 'i'}},
                {'memory_type': {'$regex': 'DDR3', '$options': 'i'}}
            ]
        }))
        f.write(f"Total DDR3 items found: {len(results)}\n")
        for r in results:
            f.write(f"- [{r.get('category')}] {r.get('name')} | Type: {r.get('type')} | MoboType: {r.get('ram_type')}/{r.get('memory_type')}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
