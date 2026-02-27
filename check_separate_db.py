from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

collections = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']

output = ["Checking separate collections:"]
for c in collections:
    count = db[c].count_documents({})
    output.append(f"  {c}: {count}")

with open('separate_counts.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
