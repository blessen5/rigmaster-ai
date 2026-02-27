import os
import json
import traceback
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv

load_dotenv()

def run():
    try:
        with open('debug_log.txt', 'a') as log:
            log.write("Starting test...\n")
            
        client = MongoClient('mongodb://localhost:27017/')
        db = client['rigmaster']
        build = db.saved_builds.find_one()
        
        with open('debug_log.txt', 'a') as log:
            log.write(f"Build found: {build is not None}\n")

        # Simplified for debug
        system_role = "Say hello in JSON: {\"message\": \"hello\"}"
        user_content = "test"

        api_key = os.getenv('GEMINI_API_KEY')
        with open('debug_log.txt', 'a') as log:
             log.write(f"API Key present: {api_key is not None}\n")

        client_ai = genai.Client(api_key=api_key)
        resp = client_ai.models.generate_content(
            model='gemini-2.0-flash-exp', 
            contents=f"{system_role}\n\n{user_content}", 
            config={'response_mime_type': 'application/json'}
        )
        
        with open('resale_test_raw.txt', 'w') as f:
            f.write(resp.text)
            
        with open('debug_log.txt', 'a') as log:
            log.write("Finished successfully.\n")

    except Exception as e:
        with open('debug_log.txt', 'a') as log:
            log.write(f"ERROR: {str(e)}\n")
            log.write(traceback.format_exc())

if __name__ == "__main__":
    run()
