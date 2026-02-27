import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

try:
    print(f"Testing connection with certifi...")
    client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Connection Successful!")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
