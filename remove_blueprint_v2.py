"""
Remove blueprint sections from analysis.html using line numbers
"""
import os

file_path = 'templates/analysis.html'

# Read all lines
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines before: {len(lines)}")

# Remove HTML section (lines 395-501, 0-indexed: 394-500)
# Remove JavaScript section (lines 1036-1093, 0-indexed: 1035-1092)

# We need to remove in reverse order to preserve line numbers
# First remove JS (higher line numbers)
del lines[1035:1093]  # Remove lines 1036-1093
print(f"✅ Removed JavaScript section (lines 1036-1093)")

# Then remove HTML (lower line numbers)
del lines[394:501]  # Remove lines 395-501  
print(f"✅ Removed HTML section (lines 395-501)")

print(f"Total lines after: {len(lines)}")

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ Blueprint removal complete!")
print(f"📝 Removed {(501-395) + (1093-1036)} lines total")
