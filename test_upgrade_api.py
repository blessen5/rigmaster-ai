import requests
import json
import os

url = "http://localhost:5001/api/analyze_upgrade"
data = {
    "cpu_id": "none"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
