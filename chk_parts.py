from pymongo import MongoClient
import os

def check_problematic_items():
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(MONGO_URI)
    db = client['rigmaster']
    
    parts = [
        ("cpus", "13900KF"),
        ("gpus", "4070 TI SUPER"),
        ("motherboards", "Z790 CARBON"),
        ("ram", "64GB"),
        ("storage", "990 PRO 4TB"),
        ("psu", "RM1000X"),
        ("cases", "5000D"),
        ("coolers", "H170i")
    ]
    
    for col, name in parts:
        print(f"--- Searching in {col} for '{name}' ---")
        items = list(db[col].find({"name": {"$regex": name, "$options": "i"}}))
        for i in items:
            print(f"ID: {i['_id']} | Name: {i.get('name')} | Price: {i.get('price')} | Status: {i.get('status')}")

if __name__ == "__main__":
    check_problematic_items()
