
with open('app.py', 'r') as f:
    lines = f.readlines()
with open('disk_check.txt', 'w') as f:
    for i in range(min(2000, len(lines))):
        if 'api_fix_compatibility' in lines[i] or 'detect_pcie' in lines[i] or 'rigmaster_detect_pcie' in lines[i]:
            f.write(f"{i+1}: {lines[i]}")
