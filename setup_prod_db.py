import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def setup_database():
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db = client['rigmaster']
    
    print(f"🚀 Initializing RigMaster Database at {mongo_uri}")
    
    # 1. Create Indexes (Crucial for performance with 20k+ items)
    print("📌 Creating indexes...")
    db.components.create_index([("category", 1)])
    db.components.create_index([("name", "text")]) # For search
    db.components.create_index([("price", 1)])
    db.users.create_index([("username", 1)], unique=True)
    db.users.create_index([("email", 1)], unique=True)
    
    # 2. Add Starter Admin User if none exists
    if db.users.count_documents({"is_admin": True}) == 0:
        print("👤 No admin found. You should register an account and then promote it to admin via the Mongo shell or a script.")
        # Alternatively, we could create a default one, but it's safer to let the user register.

    # 3. Migration Logic (Optional: Transfer from old separate collections to unified)
    old_cols = {
        'cpus': 'cpu', 'gpus': 'gpu', 'motherboards': 'motherboard', 
        'ram': 'ram', 'storage': 'storage', 'psu': 'psu', 
        'cases': 'case', 'coolers': 'cooler'
    }
    
    migrated_count = 0
    for old_col, cat_name in old_cols.items():
        count = db[old_col].count_documents({})
        if count > 0:
            print(f"📦 Migrating {count} items from '{old_col}' to unified 'components'...")
            items = list(db[old_col].find())
            for item in items:
                # Check if already exists in unified
                if not db.components.find_one({"name": item['name'], "category": cat_name}):
                    item['category'] = cat_name
                    # Remove original _id if it was an ObjectId from another collection to avoid collisions
                    if '_id' in item: del item['_id'] 
                    db.components.insert_one(item)
                    migrated_count += 1
            # Optional: Clear old collection after migration
            # db[old_col].drop()
    
    if migrated_count > 0:
        print(f"✅ Migrated {migrated_count} items.")

    # 4. Add Essential Accessories (The 4 New Categories) if empty
    new_cats = {
        'fans': [
            {"name": "Corsair LL120 RGB 3-Pack", "brand": "Corsair", "price": 120, "status": "Active"},
            {"name": "Noctua NF-F12 PWM", "brand": "Noctua", "price": 25, "status": "Active"},
            {"name": "Lian Li Uni Fan SL-Infinity", "brand": "Lian Li", "price": 30, "status": "Active"}
        ],
        'monitor': [
            {"name": "Samsung Odyssey G7 28\" 4K 144Hz", "brand": "Samsung", "price": 650, "status": "Active"},
            {"name": "LG UltraGear 27GP850-B 1440p", "brand": "LG", "price": 350, "status": "Active"},
            {"name": "ASUS TUF Gaming VG249Q 1080p", "brand": "ASUS", "price": 180, "status": "Active"}
        ],
        'os': [
            {"name": "Windows 11 Pro", "brand": "Microsoft", "price": 140, "status": "Active"},
            {"name": "Windows 11 Home", "brand": "Microsoft", "price": 110, "status": "Active"},
            {"name": "Ubuntu Desktop 24.04 LTS", "brand": "Canonical", "price": 0, "status": "Active"}
        ],
        'peripherals': [
            {"name": "Logitech G Pro X Superlight", "brand": "Logitech", "price": 150, "status": "Active"},
            {"name": "Razer BlackWidow V4 Pro", "brand": "Razer", "price": 220, "status": "Active"},
            {"name": "SteelSeries Arctis Nova Pro", "brand": "SteelSeries", "price": 350, "status": "Active"}
        ]
    }

    for cat, items in new_cats.items():
        added = 0
        for item in items:
            if not db.components.find_one({"name": item['name'], "category": cat}):
                item['category'] = cat
                item['created_at'] = datetime.now()
                db.components.insert_one(item)
                added += 1
        if added > 0:
            print(f"✨ Added {added} starter items to '{cat}' category.")

    print("\n🎉 Database setup and optimization complete!")
    print("🚀 RigMaster is ready for hosting.")

if __name__ == "__main__":
    setup_database()
