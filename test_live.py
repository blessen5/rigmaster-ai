import requests
import json

url = "http://localhost:5001/api/component-prices"
data = {
    "cpu_id": "69869a6b204f774d2814f3f0",
    "gpu_id": "69869a6e204f774d2814f799"
}

try:
    response = requests.post(url, json=data, timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
