from pymongo import MongoClient
import os

# Connect to localhost since the docker container maps 27017:27017
client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

print("Connected to MongoDB. Patching CPU sockets...")

# 1. Clear existing bad data if any (optional, but safer to overwrite)
# db.cpus.update_many({}, {'$unset': {'socket': 1}})

# 2. Apply heuristics
def patch_socket(regex, socket_name):
    result = db.components.update_many(
        {'category': 'cpu', 'name': {'$regex': regex, '$options': 'i'}}, 
        {'$set': {'socket': socket_name}}
    )
    print(f"Set socket '{socket_name}' for {result.modified_count} CPUs matching '{regex}'")

patch_socket('Ryzen', 'AM4')
patch_socket('Threadripper', 'sTRX4')
patch_socket('FX', 'AM3+')
patch_socket('Athlon', 'AM4') # Generalization
patch_socket('Core i.*-1[234]...', 'LGA1700') # 12th, 13th, 14th gen
patch_socket('Core i.*-1[01]...', 'LGA1200') # 10th, 11th gen
patch_socket('Core i.*-[6789]...', 'LGA1151') # 6th-9th gen
patch_socket('Pentium Gold', 'LGA1200') 

# Fix for the specific user error regarding "AM3" targeting
# If the Motherboard expects "AM3", we should ensure we have AM3 CPUs.
patch_socket('Phenom', 'AM3')
patch_socket('Athlon II', 'AM3')

print("Patching Motherboards...")
def patch_mobo_mem(regex, mem_type):
    result = db.components.update_many(
        {'category': 'motherboard', 'name': {'$regex': regex, '$options': 'i'}, 'memory_type': {'$exists': False}}, 
        {'$set': {'memory_type': mem_type}}
    )
    # Also fix where it might be just "2" or "4" (slots) instead of type
    result2 = db.components.update_many(
        {'category': 'motherboard', 'name': {'$regex': regex, '$options': 'i'}, 'memory_type': {'$in': ['2', '4', 2, 4]}}, 
        {'$set': {'memory_type': mem_type}}
    )
    print(f"Set RAM '{mem_type}' for {result.modified_count + result2.modified_count} Mobos matching '{regex}'")

# DDR4 Chipsets
patch_mobo_mem('A320', 'DDR4')
patch_mobo_mem('B350', 'DDR4')
patch_mobo_mem('B450', 'DDR4')
patch_mobo_mem('X370', 'DDR4')
patch_mobo_mem('X470', 'DDR4')
patch_mobo_mem('X570', 'DDR4')
patch_mobo_mem('B550', 'DDR4')
patch_mobo_mem('A520', 'DDR4')
patch_mobo_mem('Z170', 'DDR4')
patch_mobo_mem('Z270', 'DDR4')
patch_mobo_mem('Z370', 'DDR4')
patch_mobo_mem('Z390', 'DDR4')
patch_mobo_mem('B150', 'DDR4')
patch_mobo_mem('B250', 'DDR4')
patch_mobo_mem('B360', 'DDR4')
patch_mobo_mem('H110', 'DDR4')
patch_mobo_mem('H310', 'DDR4')

# DDR3 Chipsets
patch_mobo_mem('970', 'DDR3')
patch_mobo_mem('990FX', 'DDR3')
patch_mobo_mem('A960', 'DDR3')
patch_mobo_mem(' A78 ', 'DDR3')
patch_mobo_mem(' H81 ', 'DDR3')
patch_mobo_mem(' B85 ', 'DDR3')
patch_mobo_mem(' Z87 ', 'DDR3')
patch_mobo_mem(' Z97 ', 'DDR3')

# DDR5 Chipsets (Newer)
patch_mobo_mem('Z690', 'DDR5') # Some are DDR4, but usually labeled D4. Regex might be risky but better than nothing.
patch_mobo_mem('Z790', 'DDR5')
patch_mobo_mem('X670', 'DDR5')
patch_mobo_mem('B650', 'DDR5')

print("Patch complete.")
