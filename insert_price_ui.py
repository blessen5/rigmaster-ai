"""
Insert Price Tracker UI into analysis.html
"""

# Read the UI HTML
with open('price_tracker_ui.html', 'r', encoding='utf-8') as f:
    ui_html = f.read()

# Read analysis.html
with open('templates/analysis.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the insertion point (before the loading-msg div)
insertion_marker = '            <div id="loading-msg"'
insertion_index = content.find(insertion_marker)

if insertion_index != -1:
    # Insert the UI before the loading message
    new_content = content[:insertion_index] + ui_html + '\n' + content[insertion_index:]
    
    # Write back
    with open('templates/analysis.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Price Tracker UI inserted successfully!")
    print(f"📝 Inserted at position {insertion_index}")
else:
    print("⚠️  Could not find insertion point")
