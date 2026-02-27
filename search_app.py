
import os

with open('app.py', 'rb') as f:
    content = f.read().decode('utf-8')
    
lines = content.splitlines()
with open('search_res.txt', 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines):
        if 'def get_component_list' in line:
            f.write(f"{i+1}: {line}\n")
