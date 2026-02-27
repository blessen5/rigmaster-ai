from pymongo import MongoClient
import os

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    
    component_cols = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers', 'components']
    
    with open('counts_detailed.txt', 'w') as f:
        total = 0
        for col in component_cols:
            count = db[col].count_documents({})
            f.write(f"{col}: {count}\n")
            if col != 'components':
                total += count
        f.write(f"\nSum of category collections: {total}\n")
        
except Exception as e:
    with open('counts_detailed.txt', 'w') as f:
        f.write(f"Error: {e}")
