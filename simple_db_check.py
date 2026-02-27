from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
build = db.saved_builds.find_one()

if build:
    print(f"Build ID: {build.get('_id')}")
    print(f"Name: {build.get('name')}")
    print(f"CPU ID: {build.get('cpu_id')}")
    # ...
else:
    print("No builds found.")
