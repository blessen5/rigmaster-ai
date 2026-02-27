from pymongo import MongoClient
import os
import json
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017/')

results = {
    "uri": MONGO_URI,
    "collections": [],
    "samples": {},
    "gaps": {}
}

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client['rigmaster']
    
    results["collections"] = db.list_collection_names()
    
    if 'components' in results["collections"]:
        # Sample docs
        docs = list(db.components.find().limit(3))
        for i, doc in enumerate(docs):
            doc['_id'] = str(doc['_id'])
            results["samples"][f"sample_{i}"] = doc
            
        categories = db.components.distinct('category')
        results["categories"] = categories
        
        for cat in categories:
            cat_info = {}
            sample = db.components.find_one({'category': cat})
            if sample:
                fields = list(sample.keys())
                cat_info["fields"] = fields
                cat_info["missing"] = {}
                
                for field in fields:
                    if field == '_id': continue
                    count_missing = db.components.count_documents({
                        'category': cat,
                        '$or': [
                            {field: None},
                            {field: ""},
                            {field: {"$exists": False}}
                        ]
                    })
                    if count_missing > 0:
                        cat_info["missing"][field] = count_missing
                
                # Check for critical fields that SHOULD exist but might be missing entirely
                critical_fields = ['price', 'brand', 'name', 'status']
                if cat == 'cpu': critical_fields += ['socket', 'cores', 'threads']
                if cat == 'gpu': critical_fields += ['chipset', 'vram']
                
                for cf in critical_fields:
                    if cf not in fields:
                        count_cf_missing = db.components.count_documents({'category': cat})
                        cat_info["missing"][cf] = count_cf_missing
            
            results["gaps"][cat] = cat_info
    else:
        results["error"] = "components collection not found"
        
except Exception as e:
    results["exception"] = str(e)

with open('db_gaps.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Done")
