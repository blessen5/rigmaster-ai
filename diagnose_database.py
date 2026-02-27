from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['rigmaster']

print("\n" + "=" * 70)
print("DATABASE DIAGNOSTIC REPORT")
print("=" * 70)

categories = ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler']

total = 0
for cat in categories:
    count = db.components.count_documents({'category': cat})
    total += count
    print(f"\n{cat.upper()}: {count} components")
    
    if count > 0:
        # Show top 3 most expensive
        top_3 = list(db.components.find({'category': cat}).sort('price', -1).limit(3))
        print("  Top 3 most expensive:")
        for item in top_3:
            print(f"    • {item.get('name', 'Unknown')} - ${item.get('price', 'N/A')}")
    else:
        print("  ❌ EMPTY - No components found!")

print("\n" + "=" * 70)
print(f"TOTAL: {total} components")
print("=" * 70)

if total == 0:
    print("\n❌ DATABASE IS EMPTY!")
    print("\nRun this to populate:")
    print("  python add_massive_database.py")
elif total < 100:
    print("\n⚠️  LOW COMPONENT COUNT")
    print(f"   Only {total} components found.")
    print("\nRun this to add more:")
    print("  python add_massive_database.py")
else:
    print("\n✅ Database has sufficient components!")
    
    # Check for high-end components
    rtx_4090 = db.components.find_one({'category': 'gpu', 'name': {'$regex': 'RTX 4090', '$options': 'i'}})
    i9_14900k = db.components.find_one({'category': 'cpu', 'name': {'$regex': 'i9-14900', '$options': 'i'}})
    
    if rtx_4090:
        print(f"   ✅ Found high-end GPU: {rtx_4090['name']} (${rtx_4090['price']})")
    else:
        print("   ⚠️  No RTX 4090 found - may need to import high-end components")
    
    if i9_14900k:
        print(f"   ✅ Found high-end CPU: {i9_14900k['name']} (${i9_14900k['price']})")
    else:
        print("   ⚠️  No i9-14900K found - may need to import high-end components")

print("\n")
