import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
c = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = c['rigmaster']
with open('db_stats.txt', 'w') as f:
    f.write(f"Users: {db.users.count_documents({})}\n")
    f.write(f"Builds: {db.saved_builds.count_documents({})}\n")
    f.write(f"Components: {db.components.count_documents({})}\n")
    f.write(f"AI: {db.ai_cache.count_documents({})}\n")
