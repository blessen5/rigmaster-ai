"""
Add prices to the unified 'components' table
"""
from pymongo import MongoClient
import random

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

# Check if unified components table exists
if 'components' in db.list_collection_names():
    collection = db.components
    
    # Price ranges by category
    price_map = {
        'CPU': (50, 800),
        'GPU': (100, 2000),
        'Motherboard': (60, 500),
        'RAM': (30, 300),
        'Storage': (40, 400),
        'PSU': (40, 300),
        'Case': (30, 250),
        'Cooler': (20, 200)
    }
    
    print("Updating unified 'components' table...")
    
    # Get components without prices
    components = list(collection.find({'$or': [
        {'price': {'$exists': False}},
        {'price': None},
        {'price': 0}
    ]}))
    
    updated = 0
    for comp in components:
        category = comp.get('category', comp.get('type', 'CPU'))
        min_price, max_price = price_map.get(category, (50, 500))
        
        base_price = random.uniform(min_price, max_price)
        if random.random() > 0.5:
            price = round(base_price) - 0.01
        else:
            price = round(base_price)
        
        collection.update_one(
            {'_id': comp['_id']},
            {'$set': {
                'price': round(price, 2),
                'retailer': random.choice(['Amazon', 'Newegg', 'Best Buy', 'B&H Photo', 'Micro Center']),
                'in_stock': random.choice([True, True, True, False])
            }}
        )
        updated += 1
    
    print(f"✅ Updated {updated} components in unified table")
else:
    print("No unified 'components' table found")

print("\n🎉 Done! Refresh the Analysis page.")
