from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from datetime import datetime

mongo_uri = 'mongodb+srv://rigmaster_user:MMdm2NPf8J737U8D@cluster0.99f5zmr.mongodb.net/rigmaster?retryWrites=true&w=majority&appName=Cluster0'
db_name = 'rigmaster'

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime)):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError ("Type %s not serializable" % type(obj))

try:
    client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
    db = client[db_name]
    collections = sorted(db.list_collection_names())
    
    output_file = 'schemas_info.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for col_name in collections:
            f.write(f"\n{'='*50}\n")
            f.write(f"Collection: {col_name}\n")
            f.write(f"{'='*50}\n")
            
            sample = db[col_name].find_one()
            if sample:
                f.write("Sample Document Schema:\n")
                for key, value in sample.items():
                    val_type = type(value).__name__
                    if isinstance(value, dict):
                        f.write(f"- {key}: Object (keys: {list(value.keys())})\n")
                    elif isinstance(value, list):
                        f.write(f"- {key}: Array (length: {len(value)})\n")
                    else:
                        f.write(f"- {key}: {val_type}\n")
                
                f.write("\nRaw Sample:\n")
                f.write(json.dumps(sample, indent=4, default=json_serial))
                f.write("\n")
            else:
                f.write("No documents found in this collection.\n")
    
    print(f"Schemas written to {output_file}")

except Exception as e:
    print(f"Error: {e}")
