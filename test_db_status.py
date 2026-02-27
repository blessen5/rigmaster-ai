import requests
import json
import os

url = "http://localhost:5001/db-status"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
