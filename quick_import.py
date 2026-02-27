"""
Simple Component Import - No Dependencies
Adds high-end components directly to fix budget matching
"""

from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client['rigmaster']
    
    print("✅ MongoDB connected!")
    print("\n🚀 Adding high-end components...")
    
    # High-end components to fix budget matching
    high_end = {
        'cpus': [
            {"name": "Intel Core i9-14900K", "price": 589, "socket": "LGA1700", "cores": 24, "threads": 32, "tdp": "125W", "status": "Active"},
            {"name": "AMD Ryzen 9 7950X", "price": 549, "socket": "AM5", "cores": 16, "threads": 32, "tdp": "170W", "status": "Active"},
            {"name": "Intel Core i7-14700K", "price": 409, "socket": "LGA1700", "cores": 20, "threads": 28, "tdp": "125W", "status": "Active"},
        ],
        'gpus': [
            {"name": "NVIDIA GeForce RTX 4090", "price": 1599, "vram": "24GB GDDR6X", "tdp": "450W", "status": "Active"},
            {"name": "NVIDIA GeForce RTX 4080 SUPER", "price": 999, "vram": "16GB GDDR6X", "tdp": "320W", "status": "Active"},
            {"name": "AMD Radeon RX 7900 XTX", "price": 899, "vram": "24GB GDDR6", "tdp": "355W", "status": "Active"},
        ],
        'motherboards': [
            {"name": "ASUS ROG Maximus Z790 Hero", "price": 629, "socket": "LGA1700", "chipset": "Z790", "ram_type": "DDR5", "status": "Active"},
            {"name": "MSI MEG X670E ACE", "price": 699, "socket": "AM5", "chipset": "X670E", "ram_type": "DDR5", "status": "Active"},
        ],
        'ram': [
            {"name": "G.Skill Trident Z5 64GB DDR5-6000", "price": 229, "capacity": "64GB", "type": "DDR5", "speed": "6000 MHz", "status": "Active"},
            {"name": "Corsair Vengeance 32GB DDR5-5600", "price": 109, "capacity": "32GB", "type": "DDR5", "speed": "5600 MHz", "status": "Active"},
        ],
        'storage': [
            {"name": "Samsung 990 PRO 2TB", "price": 189, "capacity": "2TB", "type": "NVMe SSD", "status": "Active"},
            {"name": "WD Black SN850X 1TB", "price": 89, "capacity": "1TB", "type": "NVMe SSD", "status": "Active"},
        ],
        'psu': [
            {"name": "Corsair RM1000x 1000W", "price": 189, "wattage": "1000W", "efficiency": "80+ Gold", "status": "Active"},
            {"name": "EVGA 850 GT 850W", "price": 119, "wattage": "850W", "efficiency": "80+ Gold", "status": "Active"},
        ],
        'cases': [
            {"name": "Lian Li O11 Dynamic EVO", "price": 169, "form_factor": "Mid Tower", "status": "Active"},
            {"name": "NZXT H7 Flow", "price": 129, "form_factor": "Mid Tower", "status": "Active"},
        ],
        'coolers': [
            {"name": "Noctua NH-D15", "price": 119, "type": "Air Cooler", "status": "Active"},
            {"name": "Corsair H150i 360mm", "price": 289, "type": "Liquid Cooler", "status": "Active"},
        ]
    }
    
    added = 0
    for col_name, components in high_end.items():
        for comp in components:
            existing = db[col_name].find_one({"name": comp['name']})
            if not existing:
                db[col_name].insert_one(comp)
                print(f"✅ Added: {comp['name']} (${comp['price']})")
                added += 1
    
    print(f"\n✅ Added {added} high-end components!")
    
    # Show database stats
    print("\n📊 Database Summary:")
    for col in ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']:
        count = db[col].count_documents({})
        print(f"  {col.upper()}: {count} components")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n⚠️  MongoDB may not be running!")
    print("Start MongoDB and try again.")
