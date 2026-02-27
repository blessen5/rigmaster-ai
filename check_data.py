import requests
import json

# We need a session to call login_required endpoints
# But we can try to find a public build if there are any
# Or just bypass it if we can run it locally without auth (no we can't)

# I'll try to find a build ID from find_build.py output (I'll run it again and read it)
# Actually, I'll just look for a build in the DB again.
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
build = db.saved_builds.find_one()
if build:
    print(f"Testing Build ID: {build['_id']}")
    print("BUILD_DOC_START")
    import json
    from bson import json_util
    print(json_util.dumps(build, indent=2))
    print("BUILD_DOC_END")
    from app import get_build_insights_data
    # ...
    data = get_build_insights_data(build)
    print("INSIGHTS_JSON_START")
    print(json.dumps(data, indent=2))
    print("INSIGHTS_JSON_END")
else:
    print("No builds found in DB.")
