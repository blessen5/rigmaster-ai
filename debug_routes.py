from app import app

print("Registered Endpoints:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule}")

print("\nSearching for group_builder:")
if 'group_builder' in app.view_functions:
    print("Found 'group_builder' in view_functions")
else:
    print("NOT FOUND 'group_builder' in view_functions")
