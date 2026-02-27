#!/usr/bin/env python
# Diagnostic script to find syntax errors in app.py

import sys

try:
    with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Try to compile
    compile(content, 'app.py', 'exec')
    print("SUCCESS: No syntax errors found")
    
except SyntaxError as e:
    print(f"SYNTAX ERROR at line {e.lineno}:")
    print(f"  Message: {e.msg}")
    print(f"  Text: {e.text}")
    print(f"  Offset: {e.offset}")
    
    # Show context
    lines = content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(lines), e.lineno + 2)
    
    print(f"\nContext (lines {start+1}-{end}):")
    for i in range(start, end):
        marker = ">>>" if i == e.lineno - 1 else "   "
        print(f"{marker} {i+1}: {lines[i][:100]}")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
