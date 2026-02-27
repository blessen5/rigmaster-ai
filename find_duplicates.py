#!/usr/bin/env python
# Find duplicate function definitions

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all lines with 'def group_planning'
matches = []
for i, line in enumerate(lines, 1):
    if 'def group_planning' in line or '/group-planning' in line:
        matches.append((i, line.strip()))

print(f"Found {len(matches)} matches:")
for num, text in matches:
    print(f"  Line {num}: {text[:80]}")

# Also search for similar patterns
print("\nSearching for api_group routes:")
for i, line in enumerate(lines, 1):
    if 'def api_group' in line:
        print(f"  Line {i}: {line.strip()[:80]}")
