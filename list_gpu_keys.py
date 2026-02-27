from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

gpu = db.components.find_one({'category': 'gpu'})
if gpu:
    print(f"GPU Keys: {list(gpu.keys())}")
else:
    print("No GPU found")
