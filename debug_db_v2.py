import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

with open('debug_connection_v2.txt', 'w', encoding='utf-8') as f:
    f.write(f"Python Version: {sys.version}\n")
    try:
        f.write("Testing connection WITHOUT certifi...\n")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        f.write("✅ SUCCESS!\n")
    except Exception as e:
        f.write(f"❌ FAILED: {str(e)}\n")
        
        try:
             f.write("\nTesting connection with tlsAllowInvalidCertificates=True...\n")
             client = MongoClient(uri, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
             client.admin.command('ping')
             f.write("✅ SUCCESS (but insecure)!\n")
        except Exception as e2:
             f.write(f"❌ FAILED INSECURE TOO: {str(e2)}\n")
