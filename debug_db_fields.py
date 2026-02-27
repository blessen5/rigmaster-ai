from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017/')
print(f"Connecting to: {MONGO_URI}")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client['rigmaster']
    
    # Check collections
    cols = db.list_collection_names()
    print(f"Collections: {cols}")
    
    if 'components' in cols:
        print("\n--- Components Sample ---")
        docs = list(db.components.find().limit(5))
        for doc in docs:
            print(doc)
            print("-" * 20)
            
        # Analyze missing fields per category
        categories = db.components.distinct('category')
        print(f"\nCategories: {categories}")
        
        for cat in categories:
            print(f"\nAnalyzing category: {cat}")
            sample = db.components.find_one({'category': cat})
            if sample:
                fields = list(sample.keys())
                print(f"Fields found: {fields}")
                
                # Check for null or empty values in these fields for this category
                for field in fields:
                    count_missing = db.components.count_documents({
                        'category': cat,
                        '$or': [
                            {field: None},
                            {field: ""},
                            {field: {"$exists": False}}
                        ]
                    })
                    if count_missing > 0:
                        print(f"  - Field '{field}' missing/empty in {count_missing} documents")
    else:
        print("Collection 'components' not found.")
        
except Exception as e:
    print(f"Error: {e}")
