from pymongo import MongoClient
import time

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

# Map existing collections to new category names
# Keys = Old Collection Names
# Values = New 'category' field value
MAPPING = {
    'cpus': 'cpu',
    'gpus': 'gpu',
    'motherboards': 'motherboard',
    'ram': 'ram',
    'storage': 'storage',
    'psu': 'psu',
    'cases': 'case',
    'coolers': 'cooler'
}

def migrate():
    print("Starting migration to 'components' collection...")
    
    # Check if target already has data to avoid duplicates if run twice
    existing_count = db.components.count_documents({})
    if existing_count > 0:
        print(f"Warning: 'components' table already has {existing_count} items.")
        print("Dropping 'components' collection to start fresh...")
        db.components.drop()
    
    total_count = 0
    
    for old_col, new_cat in MAPPING.items():
        # Check if collection exists
        if old_col not in db.list_collection_names():
            print(f"Skipping {old_col} (not found)")
            continue

        items = list(db[old_col].find())
        if not items:
            print(f"Skipping {old_col} (empty)")
            continue
            
        print(f"Migrating {len(items)} items from '{old_col}' -> category '{new_cat}'...")
        
        # Add category field to each item
        for item in items:
            item['category'] = new_cat
            # Ensure price is numerical if possible, or leave as is. 
            # Note: _id is preserved, which is GOOD for references in saved_builds
            
        # Insert into new collection
        if items:
            db.components.insert_many(items)
            total_count += len(items)

    # Create index for performance
    print("Creating index on 'category'...")
    db.components.create_index('category')
    db.components.create_index([('category', 1), ('name', 1)])

    print(f"\nMigration Complete! {total_count} items moved to 'components' table.")
    
    # Verify
    print("\nVerification:")
    for cat in MAPPING.values():
        count = db.components.count_documents({'category': cat})
        print(f" - {cat}: {count}")

if __name__ == "__main__":
    migrate()
