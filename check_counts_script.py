
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def check_counts():
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
    db = client['rigmaster']
    
    categories = ['monitor', 'os', 'peripherals', 'fans']
    results = {}
    
    for cat in categories:
        count = db.components.count_documents({'category': cat})
        results[cat] = count
        
    with open('counts_check.txt', 'w') as f:
        for cat, count in results.items():
            f.write(f"{cat}: {count}\n")
            
if __name__ == "__main__":
    check_counts()
