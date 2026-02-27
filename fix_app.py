import os

try:
    with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    cutoff = 0
    found = False
    for i, line in enumerate(lines):
        if "app.run(host='0.0.0.0'" in line:
            cutoff = i + 1
            found = True
            break
    
    if found:
        print(f"Found cutoff at line {cutoff}")
        valid_lines = lines[:cutoff]
        
        with open('app_forgot_password_chk.py', 'r', encoding='utf-8') as f2:
            new_code = f2.read()
            
        with open('app.py', 'w', encoding='utf-8') as f:
            f.writelines(valid_lines)
            f.write("\n")
            f.write(new_code)
            
        print("Successfully fixed app.py")
    else:
        print("Could not find cutoff string in app.py")

except Exception as e:
    print(f"Error: {e}")
