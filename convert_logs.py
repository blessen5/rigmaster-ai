import os

def convert_to_utf8(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return
        
    try:
        with open(filename, 'rb') as f:
            content = f.read()
            
        # Try to detect if it's UTF-16
        if content.startswith(b'\xff\xfe') or b'\x00' in content:
            text = content.decode('utf-16')
            with open(filename + '.utf8', 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Converted {filename} to {filename}.utf8")
        else:
            print(f"{filename} seems to be UTF-8 or ASCII already")
    except Exception as e:
        print(f"Error converting {filename}: {e}")

convert_to_utf8('app.log')
convert_to_utf8('check.log')
convert_to_utf8('app_debug.log')
