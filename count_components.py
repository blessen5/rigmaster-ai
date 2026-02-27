from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

collections = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']

print("\n" + "=" * 60)
print("HARDWARE COMPONENT COUNT")
print("=" * 60)

counts = {}
for c in collections:
    count = db[c].count_documents({})
    counts[c] = count
    print(f"{c.upper():15} : {count:4} components")

total = sum(counts.values())

print("=" * 60)
print(f"TOTAL           : {total:4} components")
print("=" * 60)

# Show some examples
print("\nSample Components:")
print("-" * 60)
for c in ['cpus', 'gpus']:
    sample = db[c].find_one()
    if sample:
        print(f"\n{c.upper()} Example:")
        print(f"  Name: {sample.get('name', 'N/A')}")
        print(f"  Price: ${sample.get('price', 'N/A')}")

print("\n")
