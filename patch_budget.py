
import os

filepath = 'app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
found = False
for line in lines:
    if "budget = float(data.get('budget', 0))" in line and "api_ai_recommend" in "".join(lines[max(0, lines.index(line)-10):lines.index(line)]):
        indent = line[:line.find("budget")]
        new_lines.append(f"{indent}raw_budget = float(data.get('budget', 0))\n")
        new_lines.append(f"{indent}# Convert budget to USD for internal processing\n")
        new_lines.append(f"{indent}user_currency = session.get('currency', 'USD')\n")
        new_lines.append(f"{indent}rate = EXCHANGE_RATES.get(user_currency, 1.0)\n")
        new_lines.append(f"{indent}budget = raw_budget / rate\n")
        found = True
    else:
        new_lines.append(line)

if found:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Successfully patched app.py")
else:
    print("Could not find targets in app.py")
