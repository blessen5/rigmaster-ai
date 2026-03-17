from pymongo import MongoClient
import os
import re
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

with open("ram_analysis.txt", "w") as f:
    try:
        client = MongoClient(uri)
        db = client['rigmaster']
        
        rams = list(db.components.find({'category': 'ram'}).limit(100))
        f.write(f"Total RAM samples: {len(rams)}\n")
        
        generations = {}
        for r in rams:
            name = r.get('name', '')
            # Simple regex search
            m = re.search(r'DDR(\d)', name, re.I)
            gen = f"DDR{m.group(1)}" if m else "Unknown"
            generations[gen] = generations.get(gen, 0) + 1
            if gen == "Unknown":
                f.write(f"Unknown Gen: {name}\n")
        
        f.write(f"Generations found in first 100: {generations}\n")
        
        # Search specifically for DDR3 in all components
        all_comps = list(db.components.find({'name': {'$regex': 'DDR3', '$options': 'i'}}))
        f.write(f"All DDR3 items: {len(all_comps)}\n")
        for c in all_comps:
            f.write(f"- [{c.get('category')}] {c.get('name')}\n")
            
    except Exception as e:
        f.write(f"Error: {e}\n")
