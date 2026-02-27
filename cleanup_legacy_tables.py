from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

legacy_collections = [
    'cpus', 
    'gpus', 
    'motherboards', 
    'ram', 
    'storage', 
    'psu', 
    'cases', 
    'coolers'
]

print("Starting cleanup of legacy tables...")

deleted_count = 0
for col_name in legacy_collections:
    if col_name in db.list_collection_names():
        db[col_name].drop()
        print(f"Verified and dropped table: {col_name}")
        deleted_count += 1
    else:
        print(f"Table not found (already deleted): {col_name}")

print("-" * 30)
print(f"Cleanup complete. Removed {deleted_count} legacy tables.")

# Validation
remaining = db.list_collection_names()
print(f"\nRemaining tables ({len(remaining)}):")
print(remaining)
