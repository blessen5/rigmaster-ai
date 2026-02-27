import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
c = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = c['rigmaster']
with open('db_stats2.txt', 'w') as f:
    stats = {
        'cpus': db.components.count_documents({'category': 'cpu'}),
        'gpus': db.components.count_documents({'category': 'gpu'}),
        'motherboards': db.components.count_documents({'category': 'motherboard'}),
        'ram': db.components.count_documents({'category': 'ram'}),
        'storage': db.components.count_documents({'category': 'storage'}),
        'psu': db.components.count_documents({'category': 'psu'}),
        'cases': db.components.count_documents({'category': 'case'}),
        'coolers': db.components.count_documents({'category': 'cooler'})
    }
    total = sum(stats.values())
    f.write(f"Total By categories: {total}\n")
    for k, v in stats.items():
        f.write(f"{k}: {v}\n")
