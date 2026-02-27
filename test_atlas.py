import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

def log(msg):
    print(msg)
    with open('atlas_debug.log', 'a') as f:
        f.write(str(msg) + "\n")

if os.path.exists('atlas_debug.log'): os.remove('atlas_debug.log')

log(f"Testing connection to: {uri.split('@')[1]}")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    log("✅ Successfully connected to MongoDB Atlas!")
    
    db = client.get_database()
    log(f"📂 Selected Database: {db.name}")
    
except Exception as e:
    log(f"❌ Connection failed: {e}")
