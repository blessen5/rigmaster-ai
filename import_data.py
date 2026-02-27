import requests
import pymongo
import os
import json

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
BASE_URL = "https://raw.githubusercontent.com/docyx/pc-part-dataset/master/data/json/"

# Mapping: Collection Name -> Source JSON Filename
SOURCES = {
    'cpus': 'cpu.json',
    'gpus': 'video-card.json',
    'motherboards': 'motherboard.json',
    'ram': 'memory.json',
    'psu': 'power-supply.json',
    'storage': 'internal-hard-drive.json',
    'cases': 'case.json',
    'coolers': 'cpu-cooler.json'
}

def clean_record(record):
    """
    Clean up record to match requirements:
    - Remove pricing/availability data
    - Normalize empty values (optional)
    """
    # Remove unwanted fields
    fields_to_remove = ['price', 'features', 'ratings', 'reviews', 'link', 'merchant', 'url']
    for field in fields_to_remove:
        record.pop(field, None)
    
    # Example normalization (ensure numeric fit)
    if 'tdp' in record and record['tdp']:
        try:
            # removing 'W' if present and converting
            val = str(record['tdp']).lower().replace('w', '').strip()
            record['tdp'] = int(float(val))
        except:
            pass

    return record

def clean_record_advanced(record, type):
    """
    Advanced cleaning based on component type
    """
    record = clean_record(record)
    
    if type == 'cpus':
        # FIX: The dataset seems to miss 'socket' but has 'microarchitecture' or similar.
        # Ideally we need a better source, but for this exercise we might map known archs to sockets
        # OR just use microarchitecture as a rough proxy if the user wants "rule based".
        # However, looking at the user error "Target: AM3", the motherboard has "AM3".
        # The CPU has keys: boost_clock, core_clock, core_count, graphics, microarchitecture, tdp
        # It seems the dataset is incomplete for CPUs regarding socket.
        # Let's try to infer it or just leave it empty.
        pass
        
    return record

def import_data():
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.admin.command('ping')
        db = client['rigmaster']
        print("Connected to MongoDB.")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return

    for collection_name, filename in SOURCES.items():
        url = BASE_URL + filename
        print(f"Fetching {collection_name} data from {filename}...")
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"  [!] Failed to download {url} (Status: {response.status_code})")
                continue
            
            data = response.json()
            if not isinstance(data, list):
                print(f"  [!] Unexpected data format in {filename}")
                continue

            collection = db[collection_name]
            
            # Prepare bulk operations for efficiency and dedup logic
            operations = []
            
            for item in data:
                if 'name' not in item:
                    continue
                
                # Special fix for CPU data which is missing socket. 
                # We will attempt to use 'socket' if present, if not, we check if we can infer it.
                # Since we can't infer it easily without a lookup table, we will rely on what is there.
                # Wait! The earlier error "Target: AM3" implies the MOTHERBOARD has the data.
                # The CPU result showed: keys: [..., microarchitecture...].
                # If the dataset is truly missing socket, we can't implement the check for THIS dataset.
                # However, usually 'socket' is in the dataset.
                
                cleaned_item = clean_record(item)
                
                # Force updates to ensure new fields (if we added any logic) are applied

                
                # Perform an upsert: update if exists, insert if not
                operations.append(
                    pymongo.UpdateOne(
                        {'name': cleaned_item['name']}, 
                        {'$set': cleaned_item}, 
                        upsert=True
                    )
                )

            if operations:
                result = collection.bulk_write(operations)
                print(f"  -> Processed {len(operations)} records.")
                print(f"     Inserted: {result.upserted_count}, Modified: {result.modified_count}")
            else:
                print("  -> No valid records found to import.")

        except Exception as e:
            print(f"  [!] Error processing {collection_name}: {e}")

    print("\nApplying Data Patches (Permanent Fix)...")
    
    # 1. Patch CPU Sockets
    def patch_socket(regex, socket_name):
        res = db.components.update_many({'category': 'cpu', 'name': {'$regex': regex, '$options': 'i'}}, {'$set': {'socket': socket_name}})
        if res.modified_count > 0: print(f"  [Patch] Set CPU socket '{socket_name}' for {res.modified_count} items ({regex})")

    patch_socket('Ryzen', 'AM4')
    patch_socket('Ryzen.*7\\d{3}', 'AM5') # 7000 series
    patch_socket('Ryzen.*8\\d{3}', 'AM5') # 8000 series
    patch_socket('Ryzen.*9\\d{3}', 'AM5') # 9000 series
    patch_socket('Threadripper', 'sTRX4')
    patch_socket('FX', 'AM3+')
    patch_socket('Athlon', 'AM4') # Broad assumption for this dataset
    patch_socket('Athlon II', 'AM3')
    patch_socket('Phenom', 'AM3')
    patch_socket('Core i.*-1[234]', 'LGA1700')
    patch_socket('Core i.*-1[01]', 'LGA1200')
    patch_socket('Core i.*-[6789]', 'LGA1151')
    patch_socket('Core i.*-[45]', 'LGA1150')
    patch_socket('Core i.*-[23]', 'LGA1155')
    patch_socket('Pentium Gold', 'LGA1700') # Some are 1200, some 1700 - assumption


    # 2. Patch Motherboard Memory Types
    def patch_mobo_mem(regex, mem_type):
        res = db.components.update_many(
            {'category': 'motherboard', 'name': {'$regex': regex, '$options': 'i'}}, 
            {'$set': {'memory_type': mem_type}}
        )
        if res.modified_count > 0: print(f"  [Patch] Set Mobo RAM '{mem_type}' for {res.modified_count} items ({regex})")

    # DDR4
    for chipset in ['A320', 'B350', 'B450', 'X370', 'X470', 'X570', 'B550', 'A520', 'Z170', 'Z270', 'Z370', 'Z390', 'B150', 'B250', 'B360', 'H110', 'H310']:
        patch_mobo_mem(chipset, 'DDR4')
        
    # DDR3
    for chipset in ['970', '990FX', 'A960', 'A78', 'H81', 'B85', 'Z87', 'Z97']:
        patch_mobo_mem(chipset, 'DDR3')
        
    # DDR5
    for chipset in ['Z690', 'Z790', 'X670', 'B650']:
        patch_mobo_mem(chipset, 'DDR5')

    print("\nData import and patching completed.")

if __name__ == "__main__":
    import_data()
