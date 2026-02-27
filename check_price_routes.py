"""
Test if the route is actually registered in Flask
"""
import sys
sys.path.insert(0, '.')

from app import app

print("=" * 60)
print("CHECKING REGISTERED ROUTES")
print("=" * 60)

# List all routes
routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'endpoint': rule.endpoint,
        'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
        'path': rule.rule
    })

# Sort by path
routes.sort(key=lambda x: x['path'])

# Check for price tracker routes
price_routes = [r for r in routes if 'price' in r['path'].lower()]

print(f"\nTotal routes: {len(routes)}")
print(f"Price-related routes: {len(price_routes)}\n")

if price_routes:
    print("✅ PRICE TRACKER ROUTES FOUND:")
    for route in price_routes:
        print(f"  {route['methods']:8} {route['path']}")
else:
    print("❌ NO PRICE TRACKER ROUTES FOUND")
    print("\nSearching for 'component' in routes...")
    comp_routes = [r for r in routes if 'component' in r['path'].lower()]
    if comp_routes:
        for route in comp_routes:
            print(f"  {route['methods']:8} {route['path']}")
    else:
        print("  None found")

print("\n" + "=" * 60)
