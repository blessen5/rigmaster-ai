"""
Script to remove all Hardware Blueprint code from analysis.html
"""

# Read the file
with open('templates/analysis.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove the blueprint HTML section (lines 395-501)
lines = content.split('\n')

# Find start and end of blueprint section
start_marker = '<!-- HARDWARE BLUEPRINT & EXPANSION MAP (New Feature) -->'
end_marker_line = None

start_line = None
for i, line in enumerate(lines):
    if start_marker in line:
        start_line = i
    if start_line is not None and '</div>' in line and 'blueprint-lab' in lines[start_line:i+1][-10:]:
        # Found the closing div for blueprint-lab
        end_marker_line = i
        break

if start_line and end_marker_line:
    # Remove the section
    del lines[start_line:end_marker_line+2]  # +2 to include closing div and blank line
    print(f"✅ Removed HTML section (lines {start_line+1} to {end_marker_line+2})")
else:
    print("⚠️  Could not find blueprint HTML section")

# Rejoin content
content = '\n'.join(lines)

# Now remove the JavaScript section
js_start = content.find('// --- 5. Hardware Blueprint & Expansion Inventory (New) ---')
if js_start != -1:
    # Find the end of this section (next major comment or end of validateBuild function)
    js_end = content.find('} catch (e) { console.error(\'Performance analysis failed\'', js_start)
    if js_end == -1:
        js_end = content.find('// --- 6.', js_start)
    
    if js_end != -1:
        # Remove this section
        content = content[:js_start] + content[js_end:]
        print("✅ Removed JavaScript blueprint fetch code")
    else:
        print("⚠️  Could not find end of blueprint JavaScript")
else:
    print("⚠️  Could not find blueprint JavaScript section")

# Write back
with open('templates/analysis.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Blueprint code removal complete!")
print("📝 File: templates/analysis.html updated")
