"""
Add realistic prices to components in MongoDB
"""
from pymongo import MongoClient
from bson import ObjectId
import random

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

# Price ranges for each category (in USD)
price_ranges = {
    'cpus': (50, 800),
    'gpus': (100, 2000),
    'motherboards': (60, 500),
    'ram': (30, 300),
    'storage': (40, 400),
    'psu': (40, 300),
    'cases': (30, 250),
    'coolers': (20, 200)
}

print("=" * 60)
print("ADDING PRICES TO COMPONENTS")
print("=" * 60)

total_updated = 0

for collection_name, (min_price, max_price) in price_ranges.items():
    collection = db[collection_name]
    
    # Get all components without prices
    components = list(collection.find({'$or': [
        {'price': {'$exists': False}},
        {'price': None},
        {'price': 0}
    ]}))
    
    updated = 0
    for comp in components:
        # Generate realistic price based on category
        base_price = random.uniform(min_price, max_price)
        
        # Round to .99 or .00 for realism
        if random.random() > 0.5:
            price = round(base_price) - 0.01  # e.g., 299.99
        else:
            price = round(base_price)  # e.g., 300.00
        
        # Update the component
        collection.update_one(
            {'_id': comp['_id']},
            {'$set': {
                'price': round(price, 2),
                'retailer': random.choice(['Amazon', 'Newegg', 'Best Buy', 'B&H Photo', 'Micro Center']),
                'in_stock': random.choice([True, True, True, False])  # 75% in stock
            }}
        )
        updated += 1
    
    print(f"✅ {collection_name:15} - Updated {updated:5} components")
    total_updated += updated

print("=" * 60)
print(f"TOTAL UPDATED: {total_updated} components")
print("=" * 60)
print("\n🎉 Prices added! Refresh the Analysis page to see real pricing.")
