import requests
import json

# Test if the route exists
url = "http://localhost:5001/api/build-blueprint"
test_data = {
    "cpu_id": "69869a6b204f774d2814f2a9",
    "motherboard_id": "69869a79204f774d28151059",
    "ram_id": "69869a87204f774d2815223c"
}

print("Testing /api/build-blueprint endpoint...")
print(f"URL: {url}")
print(f"Data: {json.dumps(test_data, indent=2)}\n")

try:
    response = requests.post(url, json=test_data, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")
    
    if response.status_code == 404:
        print("❌ ROUTE NOT FOUND (404)")
        print("Response body:")
        print(response.text[:500])
    else:
        print("✅ Route exists!")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
except Exception as e:
    print(f"❌ Error: {e}")
