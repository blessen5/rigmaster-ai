import requests
import json
import os

url = "http://localhost:5001/api/build-blueprint"
data = {
    "cpu_id": "none",
    "motherboard_id": "none",
    "ram_id": "none"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
