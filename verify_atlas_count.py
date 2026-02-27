import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
c = MongoClient(os.getenv('MONGO_URI'))
count = c['rigmaster']['components'].count_documents({})
with open('verify_count.json', 'w') as f:
    json.dump({"count": count}, f)
print("Done")
