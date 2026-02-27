from app import app
import sys

print("--- REGISTERED ENDPOINTS ---")
found_group_planning = False
found_group_builder = False

for rule in app.url_map.iter_rules():
    print(f"Endpoint: {rule.endpoint} -> {rule}")
    if 'group_planning' in rule.endpoint:
        found_group_planning = True
    if 'group_builder' in rule.endpoint:
        found_group_builder = True

print("-" * 30)
if found_group_planning:
    print("ALERT: 'group_planning' endpoint exists!")
else:
    print("OK: 'group_planning' endpoint NOT found.")

if found_group_builder:
    print("OK: group_builder endpoint exists.")
else:
    print("ALERT: group_builder endpoint NOT found.")
