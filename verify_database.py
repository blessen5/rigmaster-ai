"""
Quick Database Verification Script
Checks how many components are in the database
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['rigmaster']

print("=" * 70)
print("📊 DATABASE VERIFICATION REPORT")
print("=" * 70)

collections = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']

total_components = 0

for col_name in collections:
    count = db[col_name].count_documents({})
    total_components += count
    
    # Get price range
    if count > 0:
        min_price_doc = db[col_name].find_one(sort=[('price', 1)])
        max_price_doc = db[col_name].find_one(sort=[('price', -1)])
        
        min_price = min_price_doc.get('price', 0) if min_price_doc else 0
        max_price = max_price_doc.get('price', 0) if max_price_doc else 0
        
        print(f"\n{col_name.upper()}: {count} components")
        print(f"  Price range: ${min_price} - ${max_price}")
        
        # Show 3 sample components
        samples = list(db[col_name].find().limit(3))
        for sample in samples:
            print(f"  • {sample.get('name', 'Unknown')} - ${sample.get('price', 'N/A')}")
    else:
        print(f"\n{col_name.upper()}: ❌ NO COMPONENTS")

print("\n" + "=" * 70)
print(f"TOTAL COMPONENTS: {total_components}")
print("=" * 70)

if total_components == 0:
    print("\n⚠️  Database is empty!")
    print("Run one of these scripts to populate:")
    print("  • python add_massive_database.py")
    print("  • python add_comprehensive_components.py")
    print("  • python import_from_sources.py")
elif total_components < 50:
    print("\n⚠️  Low component count. Consider running:")
    print("  • python add_massive_database.py (300+ components)")
else:
    print("\n✅ Database looks good!")
    print(f"   You have {total_components} components ready to use.")
    print("   Restart your Flask app and test AI recommendations!")
