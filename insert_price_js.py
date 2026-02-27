"""
Insert Price Tracker JavaScript into analysis.html
"""

# Read the JS code
with open('price_tracker_js.txt', 'r', encoding='utf-8') as f:
    js_code = f.read()

# Read analysis.html
with open('templates/analysis.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the insertion point (after eco analysis, before performance analysis)
# Look for the eco analysis catch block
insertion_marker = "} catch (e) { console.error('Eco analysis failed:', e); }"
insertion_index = content.find(insertion_marker)

if insertion_index != -1:
    # Find the end of that line
    end_of_line = content.find('\n', insertion_index)
    
    # Insert the JS after the eco analysis section
    new_content = content[:end_of_line+1] + js_code + content[end_of_line+1:]
    
    # Write back
    with open('templates/analysis.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Price Tracker JavaScript inserted successfully!")
    print(f"📝 Inserted after eco analysis section")
else:
    print("⚠️  Could not find insertion point")
    print("Searching for alternative marker...")
    
    # Try alternative marker
    alt_marker = "// --- 6. Performance Analysis"
    alt_index = content.find(alt_marker)
    if alt_index != -1:
        new_content = content[:alt_index] + js_code + '\n' + content[alt_index:]
        with open('templates/analysis.html', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Price Tracker JavaScript inserted (alternative location)!")
    else:
        print("❌ Could not find any suitable insertion point")
