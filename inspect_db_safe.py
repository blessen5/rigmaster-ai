import sys
import traceback
from pymongo import MongoClient
import os

try:
    with open("inspect_out.txt", "w") as f:
        f.write("Starting inspection\n")
        
        MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        f.write(f"Connecting to {MONGO_URI}\n")
        
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client['rigmaster']
        
        collections = ['cpus', 'gpus', 'ram', 'storage', 'psu']
        
        for col_name in collections:
            f.write(f"--- {col_name} ---\n")
            try:
                doc = db[col_name].find_one()
                if doc:
                    filtered = {k: v for k, v in doc.items() if 'tdp' in k.lower() or 'watt' in k.lower() or 'power' in k.lower()}
                    f.write(f"Sample keys: {list(doc.keys())}\n")
                    f.write(f"Power related: {filtered}\n")
                else:
                    f.write("Empty collection\n")
            except Exception as e:
                f.write(f"Error reading collection {col_name}: {e}\n")
            f.write("\n")
            
        f.write("Done.\n")

except Exception as e:
    with open("inspect_error.txt", "w") as err:
        err.write(traceback.format_exc())
