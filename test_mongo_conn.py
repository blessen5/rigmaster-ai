from pymongo import MongoClient
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    print("SUCCESS: MongoDB is connected.")
except Exception as e:
    print(f"FAILED: Could not connect to MongoDB. Error: {e}")
