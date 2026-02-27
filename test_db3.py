import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
c = MongoClient(os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017/'))
db = c['rigmaster']
res = list(db.components.aggregate([{'$group': {'_id': '$category', 'count': {'$sum': 1}}}]))
for r in res:
    print(f"{r['_id']}: {r['count']}")
