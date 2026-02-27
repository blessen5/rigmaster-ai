import requests
import json
from pymongo import MongoClient

def run_diag():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    build = db.saved_builds.find_one()
    
    if not build:
        print("No builds found.")
        return

    build_id = str(build['_id'])
    print(f"Testing API for Build: {build_id}")
    
    # We can't easily call the API with auth here, but we can call the function directly
    import app
    # Inject a dummy session if needed, but get_build_insights_data doesn't use it
    
    data = app.get_build_insights_data(build)
    print("Function result keys:", list(data.keys()))
    print("Assembly steps length:", len(data.get('assembly_steps', [])))
    print("Setup checklist length:", len(data.get('setup_checklist', [])))
    
    # Print the first few steps
    if data.get('assembly_steps'):
        print("First step:", data['assembly_steps'][0])
    
run_diag()
