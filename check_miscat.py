from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

# Search for any component that looks like a GPU but isn't categorized as 'gpu'
gpu_keywords = ['RTX', 'GTX', 'Radeon', 'GeForce', 'Intel Arc']
found = []

for keyword in gpu_keywords:
    items = db.components.find({
        'name': {'$regex': keyword, '$options': 'i'},
        'category': {'$ne': 'gpu'}
    }, {'name': 1, 'category': 1})
    for item in items:
        found.append(f"'{item['name']}' is categorized as '{item['category']}'")

with open('miscat_gpus.txt', 'w', encoding='utf-8') as f:
    if found:
        f.write('\n'.join(found))
    else:
        f.write("No miscategorized GPUs found.")
