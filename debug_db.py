import os
import sys
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

with open('debug_connection.txt', 'w', encoding='utf-8') as f:
    f.write(f"Python Version: {sys.version}\n")
    f.write(f"Certifi Path: {certifi.where()}\n")
    try:
        f.write("Testing connection...\n")
        client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        f.write("✅ SUCCESS!\n")
    except Exception as e:
        f.write(f"❌ FAILED: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())
