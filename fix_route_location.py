"""
Move Price Tracker routes to the correct location in app.py
(before the if __name__ == '__main__' block)
"""

# Read app.py
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the price tracker routes (lines 3794-4008)
# Find the if __name__ block (line 3788)

# Extract the price tracker section
price_tracker_start = None
price_tracker_end = None
main_block_line = None

for i, line in enumerate(lines):
    if "# PRICE TRACKER FEATURE - Real-Time Component Pricing" in line:
        price_tracker_start = i
    if price_tracker_start and i > price_tracker_start + 200:  # End of file
        price_tracker_end = len(lines)
        break
    if "if __name__ == '__main__':" in line:
        main_block_line = i

if price_tracker_start and main_block_line:
    print(f"Found Price Tracker routes at line {price_tracker_start + 1}")
    print(f"Found main block at line {main_block_line + 1}")
    
    # Extract the price tracker code
    price_tracker_code = lines[price_tracker_start:price_tracker_end]
    
    # Remove from current location
    del lines[price_tracker_start:price_tracker_end]
    
    # Recalculate main block line after deletion
    main_block_line = None
    for i, line in enumerate(lines):
        if "if __name__ == '__main__':" in line:
            main_block_line = i
            break
    
    # Insert before the main block
    lines = lines[:main_block_line] + price_tracker_code + ['\n\n'] + lines[main_block_line:]
    
    # Write back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Moved Price Tracker routes before main block!")
    print(f"📝 Routes now at line {main_block_line + 1}")
else:
    print("❌ Could not find routes or main block")
