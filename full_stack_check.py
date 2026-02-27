from pymongo import MongoClient
import requests
import json
import os

def check_mongodb():
    print("Checking MongoDB...")
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        db = client['rigmaster']
        count = db.components.count_documents({})
        print(f"✅ MongoDB: Connected. Found {count} components in 'rigmaster.components'.")
        
        # Check categories
        for cat in ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler']:
            c = db.components.count_documents({'category': cat})
            print(f"   - {cat}: {c}")
            
    except Exception as e:
        print(f"❌ MongoDB: Error - {e}")

def check_app_running():
    print("\nChecking if RigMaster app is responsive...")
    try:
        # Try both 5000 and 5001 just in case
        for port in [5000, 5001]:
            try:
                r = requests.get(f'http://127.0.0.1:{port}/db-status', timeout=3)
                print(f"✅ App (Port {port}): Response {r.status_code} - {r.text}")
                
                # Test component API
                r2 = requests.get(f'http://127.0.0.1:{port}/api/cpus', timeout=3)
                if r2.status_code == 200:
                    data = r2.json()
                    print(f"✅ App (Port {port}): /api/cpus returned {len(data)} items.")
                else:
                    print(f"❌ App (Port {port}): /api/cpus failed - {r2.status_code}")
                return
            except requests.exceptions.ConnectionError:
                continue
        print("❌ App: No response on port 5000 or 5001. Is it running?")
    except Exception as e:
        print(f"❌ App: Error during check - {e}")

if __name__ == "__main__":
    check_mongodb()
    check_app_running()
