import sys
sys.path.insert(0, r'c:\Users\bless\.gemini\antigravity\scratch\rigmaster-ui')

from app import app

print("=" * 60)
print("REGISTERED ROUTES IN CURRENT APP")
print("=" * 60)

routes = []
for rule in app.url_map.iter_rules():
    routes.append((rule.rule, ','.join(rule.methods - {'HEAD', 'OPTIONS'})))

# Sort and display
routes.sort()
for route, methods in routes:
    print(f"{route:50} [{methods}]")

print("\n" + "=" * 60)

# Specifically check for blueprint route
blueprint_found = any('/api/build-blueprint' in route for route, _ in routes)
print(f"\n/api/build-blueprint route found: {blueprint_found}")

if not blueprint_found:
    print("\n⚠️  WARNING: Blueprint route is NOT registered!")
    print("This means the app.py file being run is outdated.")
