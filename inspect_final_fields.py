from pymongo import MongoClient
import json
from bson import ObjectId
from datetime import datetime

def default_serializer(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

collections = ['components', 'users', 'saved_builds', 'shopping_cache', 'ai_cache', 'otps']

output = []

for col_name in collections:
    output.append(f"### Table: {col_name}")
    doc = db[col_name].find_one()
    if doc:
        # Get keys sorted
        keys = sorted(list(doc.keys()))
        output.append(f"**Fields:** `{', '.join(keys)}`")
        
        # Show a sample value for context
        sample_subset = {k: (str(doc[k])[:50] + '...' if len(str(doc[k])) > 50 else doc[k]) for k in keys[:5]} 
        # output.append(f"Sample: {json.dumps(sample_subset, default=default_serializer)}")
        
        if col_name == 'components':
            output.append("*(Note: This is a unified table. Fields like 'socket' or 'vram' appear based on the 'category' field)*")
    else:
        output.append("*(Empty Table)*")
    output.append("")

print("\n".join(output))
