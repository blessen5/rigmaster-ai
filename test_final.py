import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

def test():
    with open('atlas_final.log', 'w') as log:
        try:
            load_dotenv()
            uri = os.getenv('MONGO_URI')
            log.write(f"URI found in .env\n")
            
            # Simple check if srv is supported
            try:
                import dns
                log.write("dnspython is installed\n")
            except:
                log.write("dnspython NOT found\n")
            
            client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            log.write("Client object created. Pinging...\n")
            
            client.admin.command('ping')
            log.write("✅ PING SUCCESSFUL!\n")
            
            db = client.get_database()
            log.write(f"Connected to DB: {db.name}\n")
            
        except Exception as e:
            log.write(f"❌ ERROR: {e}\n")

if __name__ == "__main__":
    test()
