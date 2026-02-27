"""
Test the Price Tracker API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5001"

print("=" * 60)
print("TESTING PRICE TRACKER FEATURE")
print("=" * 60)

# Test data - sample component IDs
test_data = {
    "cpu_id": "69869a6b204f774d2814f2a9",
    "gpu_id": "69869a6e204f774d2814f6fe",
    "motherboard_id": "69869a79204f774d28151059",
    "ram_id": "69869a87204f774d2815223c",
    "storage_id": "69869a8f204f774d28152d6f",
    "psu_id": "69869a8b204f774d28152501",
    "case_id": "69869a98204f774d28153bfb",
    "cooler_id": "69869aa1204f774d281546e4"
}

print("\n1️⃣  Testing /api/component-prices endpoint...")
print("-" * 60)

try:
    response = requests.post(
        f"{BASE_URL}/api/component-prices",
        json=test_data,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"\nTotal Cost: ${result.get('total_cost', 0):.2f}")
        print(f"Currency: {result.get('currency', 'N/A')}")
        print(f"Components with pricing: {len(result.get('prices', {}))}")
        
        print("\nComponent Prices:")
        for category, price_data in result.get('prices', {}).items():
            price = price_data.get('price')
            if price:
                print(f"  • {category.upper()}: ${price:.2f} - {price_data.get('name', 'Unknown')}")
            else:
                print(f"  • {category.upper()}: N/A - {price_data.get('name', 'Unknown')}")
    else:
        print(f"❌ Failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n2️⃣  Testing /api/price-history/<component_id> endpoint...")
print("-" * 60)

try:
    # Test with CPU ID
    component_id = test_data['cpu_id']
    response = requests.get(
        f"{BASE_URL}/api/price-history/{component_id}",
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"\nComponent: {result.get('component_name', 'Unknown')}")
        print(f"30-Day Lowest: ${result.get('lowest_30d', 0):.2f}")
        print(f"30-Day Highest: ${result.get('highest_30d', 0):.2f}")
        print(f"30-Day Average: ${result.get('average_30d', 0):.2f}")
        print(f"History entries: {len(result.get('history', []))}")
    else:
        print(f"❌ Failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
