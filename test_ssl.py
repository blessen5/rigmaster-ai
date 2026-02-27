import os
import ssl
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_URI')

# Build a custom SSL context compatible with MongoDB Atlas + Python 3.13
def test_conn(label, **kwargs):
    try:
        c = MongoClient(uri, serverSelectionTimeoutMS=5000, **kwargs)
        c.admin.command('ping')
        res = c['rigmaster'].list_collection_names()
        print(f"SUCCESS [{label}]: Collections found = {len(res)}")
    except Exception as e:
        print(f"FAILED [{label}]: {str(e)[:120]}")

# Test 1: ssl_context with TLS 1.2 minimum
ctx = ssl.create_default_context()
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
test_conn("ssl_context_TLS1.2", ssl_context=ctx)

# Test 2: No TLS options at all
test_conn("no_extra_options")

# Test 3: tlsInsecure=True 
test_conn("tlsInsecure=True", tlsInsecure=True)
