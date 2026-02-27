
import os

with open('app.py', 'rb') as f:
    content = f.read().decode('utf-16')
    
lines = content.splitlines()
with open('routes_list.txt', 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines):
        if '@app.route' in line:
            f.write(f"{i+1}: {line}\n")
