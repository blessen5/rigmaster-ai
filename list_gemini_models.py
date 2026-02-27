import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print("Using google.genai (new sdk)...")
client = genai.Client(api_key=api_key)
try:
    # The new SDK list method
    for m in client.models.list():
        print(m.name)
except Exception as e:
    print(f"Error: {e}")
