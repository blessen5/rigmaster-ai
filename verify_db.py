from pymongo import MongoClient
import json
import sys

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    
    # Test Data 1: The user's case
    cpu_name = "Athlon X4 950" 
    mobo_name = "ASRock A320M-HDV"
    ram_name = "ADATA AD4U2400W4G17-S"

    print(f"\n--- DEBUGGING HARDWARE DATA for '{mobo_name}' ---")
    
    # FETCH CPU
    cpu = db.components.find_one({'category': 'cpu', 'name': {'$regex': cpu_name, '$options': 'i'}})
    if cpu:
        print(f"[CPU] Found: {cpu.get('name')}")
        print(f"      Socket Raw: {cpu.get('socket')}")
        print(f"      Keys: {list(cpu.keys())}")
    else:
        print(f"[CPU] NOT FOUND matching '{cpu_name}'")

    # FETCH MOBO
    mobo = db.components.find_one({'category': 'motherboard', 'name': {'$regex': mobo_name, '$options': 'i'}})
    if mobo:
        print(f"[MOBO] Found: {mobo.get('name')}")
        print(f"       MemType Raw: {mobo.get('memory_type')}")
        print(f"       MemSlots Raw: {mobo.get('memory_slots')}")
        print(f"       Socket Raw: {mobo.get('socket_cpu') or mobo.get('socket')}")
        print(f"       Keys: {list(mobo.keys())}")
    else:
        print(f"[MOBO] NOT FOUND matching '{mobo_name}'")

    # FETCH RAM
    ram = db.components.find_one({'category': 'ram', 'name': {'$regex': ram_name, '$options': 'i'}})
    if ram:
        print(f"[RAM] Found: {ram.get('name')}")
        print(f"      Type Raw: {ram.get('type')}")
        print(f"      Speed Raw: {ram.get('speed')}")
        print(f"      Keys: {list(ram.keys())}")
    else:
        print(f"[RAM] NOT FOUND matching '{ram_name}'")

except Exception as e:
    print(f"Error: {e}")
