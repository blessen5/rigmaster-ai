
import os

with open('app.py', 'rb') as f:
    raw = f.read()
    
# Try UTF-8 first
try:
    content = raw.decode('utf-8')
    encoding = 'utf-8'
except:
    content = raw.decode('utf-16')
    encoding = 'utf-16'
    
lines = content.splitlines()
with open('routes_list.txt', 'w', encoding='utf-8') as f:
    f.write(f"Detected encoding: {encoding}\n")
    for i, line in enumerate(lines):
        if '@app.route' in line:
            f.write(f"{i+1}: {line}\n")
