import os
from pymongo import MongoClient
import certifi

from dotenv import load_dotenv
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://rigmaster_user:MMdm2NPf8J737U8D@cluster0.99f5zmr.mongodb.net/rigmaster?retryWrites=true&w=majority&appName=Cluster0')

print("Connecting...")
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("Ping successful with certifi!")
except Exception as e:
    print("Certifi failed:", type(e).__name__, str(e))
    fallback_uri = MONGO_URI + "&tlsAllowInvalidCertificates=true"
    print("Trying fallback...")
    client = MongoClient(fallback_uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command('ping')
        print("Fallback ping successful!")
    except Exception as e2:
        print("Fallback failed:", type(e2).__name__, str(e2))

db = client['rigmaster']
try:
    print("components count:", db.components.count_documents({}))
except Exception as e:
    print("Failed to count:", e)
