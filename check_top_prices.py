from pymongo import MongoClient
import os

def check_top_prices():
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(MONGO_URI)
    db = client['rigmaster']
    
    cols = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']
    
    for col in cols:
        print(f"--- {col} ---")
        items = list(db[col].find().sort([('price', -1)]).limit(5))
        for i in items:
            print(f"{i.get('name')}: {i.get('price')} (Status: {i.get('status')})")

if __name__ == "__main__":
    check_top_prices()
