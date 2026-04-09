import re
import os

filepath = r'c:\Users\bless\.gemini\antigravity\scratch\rigmaster-ui\app.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# REPLACING POWER ANALYSIS CALLS
# We look for 'run_power_analysis({' and everything until the closing '})'
# using a non-greedy DOTALL match.
p_rx = re.compile(r'run_power_analysis\(\{.*?\}\)', re.DOTALL)
c_rx = re.compile(r'run_validation_logic\(\{.*?\}\)', re.DOTALL)

matches_p = p_rx.findall(content)
matches_c = c_rx.findall(content)

print(f"Found {len(matches_p)} power blocks and {len(matches_c)} validation blocks.")

new_content = p_rx.sub('run_power_analysis(build)', content)
new_content = c_rx.sub('run_validation_logic(build)', new_content)

if len(matches_p) > 0 or len(matches_c) > 0:
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_content)
    print("Success: app.py updated.")
else:
    print("Failure: No regex matches found. Check the file manually.")
