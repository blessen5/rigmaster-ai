
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def check_prices():
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
    db = client['rigmaster']
    
    categories = ['monitor', 'os', 'peripherals', 'fans']
    results = {}
    
    for cat in categories:
        sample = db.components.find_one({'category': cat, 'price': {'$exists': True, '$ne': None}})
        results[cat] = sample.get('price') if sample else "No Price Found"
        
    with open('prices_check.txt', 'w') as f:
        for cat, price in results.items():
            f.write(f"{cat}: {price}\n")
            
if __name__ == "__main__":
    check_prices()
