from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
cols = ['cpus', 'gpus', 'motherboards', 'ram', 'psu', 'storage', 'cases', 'coolers']
total = 0
results = {}
for col in cols:
    c = db[col].count_documents({})
    results[col] = c
    total += c
with open('current_total.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total: {total}\n")
    for k, v in results.items():
        f.write(f"{k}: {v}\n")
