from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
db = client['rigmaster']

def check():
    try:
        results = {}
        # Check unified collection
        results['unified_total'] = db.components.count_documents({})
        cats = ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler', 'fans', 'monitor', 'peripherals', 'os']
        results['categories'] = {cat: db.components.count_documents({'category': cat}) for cat in cats}
        
        # Check separate collections
        old_cols = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']
        results['old_cols'] = {col: db[col].count_documents({}) for col in old_cols}
        
        with open('db_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("Done")
    except Exception as e:
        with open('db_results.json', 'w') as f:
            f.write(f"Error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
