import sys
import os

# Force reload by clearing any cached imports
if 'app' in sys.modules:
    del sys.modules['app']

# Import fresh
from app import app

# Check routes
routes = [r.rule for r in app.url_map.iter_rules()]
price_routes = [r for r in routes if 'price' in r.lower()]

print(f"Total routes: {len(routes)}")
print(f"Price routes: {price_routes}")

if '/api/component-prices' in routes:
    print("\n✅ Route IS registered in app.py")
    print("❌ But running server doesn't have it - RESTART REQUIRED")
else:
    print("\n❌ Route NOT in app.py - code issue")
