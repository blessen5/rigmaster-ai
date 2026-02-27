
import re

def clean_comp_name(name):
    if not name: return "Unknown Component"
    s = str(name)
    s = re.sub(r'ID:[0-9a-fA-F]{24}\s*\|\s*', '', s)
    s = re.sub(r'\s*\|\s*Specs:\[.*?\]', '', s)
    s = s.strip(' |').strip()
    return s if s else "Unknown Component"

def get_estimated_price(comp_name, cat):
    name = str(comp_name).upper()
    if cat == 'cpus':
        if 'RYZEN 9' in name or 'CORE I9' in name: return 450
        if 'RYZEN 7' in name or 'CORE I7' in name: return 320
        if 'RYZEN 5' in name or 'CORE I5' in name: return 190
        return 120
    if cat == 'gpus':
        if '4090' in name: return 1600
        if '4080' in name or '7900 XTX' in name: return 950
        if '4070' in name or '7800 XT' in name: return 550
        if '4060' in name or '7600' in name: return 290
        return 200
    if cat == 'motherboards': return 160
    if cat == 'ram': return 90
    if cat == 'storage': return 80
    if cat == 'psu': return 110
    if cat == 'cases': return 100
    if cat == 'coolers': return 60
    return 100

def test_logic():
    key = "CPU"
    col_map = {'CPU': 'cpus'}
    
    # User Case 1: Database miss, Raw String
    comp_data = "ID:696999e41dce692221d00f2d | AMD A10-7860k"
    comp_id = "696999e41dce692221d00f2d"
    best_name = comp_data
    best_price = "---"
    
    # Simulate DB miss
    db_comp = None
    
    # Logic in app.py
    if db_comp:
        best_name = db_comp.get('name')
        # ...
        
    best_name = clean_comp_name(best_name)
    
    # Ensure price is valid
    price_raw = str(best_price).replace('$', '').replace(',', '').strip()
    use_heuristic = False
    if price_raw == "---" or not price_raw:
        use_heuristic = True
    else:
        try:
            p_num = float(price_raw)
            if p_num <= 0: use_heuristic = True
        except: use_heuristic = True
    
    if use_heuristic:
        best_price = get_estimated_price(best_name, col_map[key])
        
    print(f"Name: {best_name}")
    print(f"Price: {best_price}")
    
    if best_name == "AMD A10-7860k" and int(best_price) > 0:
        print("SUCCESS: Logic is correct.")
    else:
        print("FAILURE: Logic is flawed.")

if __name__ == "__main__":
    test_logic()
