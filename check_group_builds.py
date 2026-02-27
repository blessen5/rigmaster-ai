from app import app, db
from bson.objectid import ObjectId
import pprint

with app.app_context():
    print("--- Checking Group Builds ---")
    count = db.group_builds.count_documents({})
    print(f"Total Group Builds: {count}")
    
    builds = list(db.group_builds.find())
    for b in builds:
        print(f"\nID: {b['_id']}")
        print(f"User ID: {b.get('user_id')}")
        print(f"Name: {b.get('base_build_name')}")
        print(f"Qty: {b.get('quantity')}")
        print(f"Created: {b.get('created_at')}")

    print("\n--- Checking Saved Builds (for comparison) ---")
    saved_count = db.saved_builds.count_documents({})
    print(f"Total Saved Builds: {saved_count}")
    if saved_count > 0:
        sb = db.saved_builds.find_one()
        print(f"Sample Saved Build User ID: {sb.get('user_id')}")
