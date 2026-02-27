import os
from pymongo import MongoClient

# Base URI
uri = "mongodb+srv://rigmaster_user:MMdm2NPf8J737U8D@cluster0.99f5zmr.mongodb.net/rigmaster?retryWrites=true&w=majority&appName=Cluster0"

# Appending kwargs
# 1. Base URI 
try:
    c = MongoClient(uri, serverSelectionTimeoutMS=2000, tls=True, tlsAllowInvalidCertificates=True)
    c.admin.command('ping')
    print("SUCCESS: tls=True, tlsAllowInvalidCertificates=True")
except Exception as e:
    print(f"FAILED (kwargs): {e}")

# 2. String params
try:
    uri_str = uri + "&tls=true&tlsAllowInvalidCertificates=true"
    c2 = MongoClient(uri_str, serverSelectionTimeoutMS=2000)
    c2.admin.command('ping')
    print("SUCCESS: string params")
except Exception as e:
    print(f"FAILED (string): {e}")
