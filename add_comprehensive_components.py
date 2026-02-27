"""
Add Comprehensive Hardware Components to Database
This script adds a wide variety of PC components across all price ranges.
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['rigmaster']

print("🚀 Adding comprehensive hardware components to database...")

# ========== CPUs ==========
cpus = [
    # High-End Intel
    {"name": "Intel Core i9-14900KS", "price": 689, "socket": "LGA1700", "cores": 24, "threads": 32, "base_clock": "3.2 GHz", "boost_clock": "6.2 GHz", "tdp": "150W", "status": "Active"},
    {"name": "Intel Core i9-14900K", "price": 589, "socket": "LGA1700", "cores": 24, "threads": 32, "base_clock": "3.2 GHz", "boost_clock": "6.0 GHz", "tdp": "125W", "status": "Active"},
    {"name": "Intel Core i9-13900K", "price": 489, "socket": "LGA1700", "cores": 24, "threads": 32, "base_clock": "3.0 GHz", "boost_clock": "5.8 GHz", "tdp": "125W", "status": "Active"},
    {"name": "Intel Core i7-14700K", "price": 409, "socket": "LGA1700", "cores": 20, "threads": 28, "base_clock": "3.4 GHz", "boost_clock": "5.6 GHz", "tdp": "125W", "status": "Active"},
    {"name": "Intel Core i7-13700K", "price": 349, "socket": "LGA1700", "cores": 16, "threads": 24, "base_clock": "3.4 GHz", "boost_clock": "5.4 GHz", "tdp": "125W", "status": "Active"},
    
    # High-End AMD
    {"name": "AMD Ryzen 9 7950X3D", "price": 599, "socket": "AM5", "cores": 16, "threads": 32, "base_clock": "4.2 GHz", "boost_clock": "5.7 GHz", "tdp": "120W", "status": "Active"},
    {"name": "AMD Ryzen 9 7950X", "price": 549, "socket": "AM5", "cores": 16, "threads": 32, "base_clock": "4.5 GHz", "boost_clock": "5.7 GHz", "tdp": "170W", "status": "Active"},
    {"name": "AMD Ryzen 9 7900X", "price": 429, "socket": "AM5", "cores": 12, "threads": 24, "base_clock": "4.7 GHz", "boost_clock": "5.4 GHz", "tdp": "170W", "status": "Active"},
    {"name": "AMD Ryzen 7 7800X3D", "price": 449, "socket": "AM5", "cores": 8, "threads": 16, "base_clock": "4.2 GHz", "boost_clock": "5.0 GHz", "tdp": "120W", "status": "Active"},
    {"name": "AMD Ryzen 7 7700X", "price": 329, "socket": "AM5", "cores": 8, "threads": 16, "base_clock": "4.5 GHz", "boost_clock": "5.4 GHz", "tdp": "105W", "status": "Active"},
    
    # Mid-Range Intel
    {"name": "Intel Core i5-14600K", "price": 319, "socket": "LGA1700", "cores": 14, "threads": 20, "base_clock": "3.5 GHz", "boost_clock": "5.3 GHz", "tdp": "125W", "status": "Active"},
    {"name": "Intel Core i5-13600K", "price": 289, "socket": "LGA1700", "cores": 14, "threads": 20, "base_clock": "3.5 GHz", "boost_clock": "5.1 GHz", "tdp": "125W", "status": "Active"},
    {"name": "Intel Core i5-14400F", "price": 199, "socket": "LGA1700", "cores": 10, "threads": 16, "base_clock": "2.5 GHz", "boost_clock": "4.7 GHz", "tdp": "65W", "status": "Active"},
    
    # Mid-Range AMD
    {"name": "AMD Ryzen 5 7600X", "price": 249, "socket": "AM5", "cores": 6, "threads": 12, "base_clock": "4.7 GHz", "boost_clock": "5.3 GHz", "tdp": "105W", "status": "Active"},
    {"name": "AMD Ryzen 5 5600X", "price": 149, "socket": "AM4", "cores": 6, "threads": 12, "base_clock": "3.7 GHz", "boost_clock": "4.6 GHz", "tdp": "65W", "status": "Active"},
    
    # Budget
    {"name": "Intel Core i3-14100F", "price": 119, "socket": "LGA1700", "cores": 4, "threads": 8, "base_clock": "3.5 GHz", "boost_clock": "4.7 GHz", "tdp": "58W", "status": "Active"},
    {"name": "AMD Ryzen 5 5500", "price": 99, "socket": "AM4", "cores": 6, "threads": 12, "base_clock": "3.6 GHz", "boost_clock": "4.2 GHz", "tdp": "65W", "status": "Active"},
]

# ========== GPUs ==========
gpus = [
    # Ultra High-End NVIDIA
    {"name": "NVIDIA GeForce RTX 4090", "price": 1599, "vram": "24GB GDDR6X", "tdp": "450W", "cuda_cores": 16384, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4080 SUPER", "price": 999, "vram": "16GB GDDR6X", "tdp": "320W", "cuda_cores": 10240, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4080", "price": 949, "vram": "16GB GDDR6X", "tdp": "320W", "cuda_cores": 9728, "status": "Active"},
    
    # High-End NVIDIA
    {"name": "NVIDIA GeForce RTX 4070 Ti SUPER", "price": 799, "vram": "16GB GDDR6X", "tdp": "285W", "cuda_cores": 8448, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4070 Ti", "price": 749, "vram": "12GB GDDR6X", "tdp": "285W", "cuda_cores": 7680, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4070 SUPER", "price": 599, "vram": "12GB GDDR6X", "tdp": "220W", "cuda_cores": 7168, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4070", "price": 549, "vram": "12GB GDDR6X", "tdp": "200W", "cuda_cores": 5888, "status": "Active"},
    
    # High-End AMD
    {"name": "AMD Radeon RX 7900 XTX", "price": 899, "vram": "24GB GDDR6", "tdp": "355W", "stream_processors": 6144, "status": "Active"},
    {"name": "AMD Radeon RX 7900 XT", "price": 749, "vram": "20GB GDDR6", "tdp": "315W", "stream_processors": 5376, "status": "Active"},
    {"name": "AMD Radeon RX 7900 GRE", "price": 649, "vram": "16GB GDDR6", "tdp": "260W", "stream_processors": 5120, "status": "Active"},
    
    # Mid-Range NVIDIA
    {"name": "NVIDIA GeForce RTX 4060 Ti 16GB", "price": 499, "vram": "16GB GDDR6", "tdp": "165W", "cuda_cores": 4352, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4060 Ti 8GB", "price": 399, "vram": "8GB GDDR6", "tdp": "160W", "cuda_cores": 4352, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4060", "price": 299, "vram": "8GB GDDR6", "tdp": "115W", "cuda_cores": 3072, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 3060", "price": 249, "vram": "12GB GDDR6", "tdp": "170W", "cuda_cores": 3584, "status": "Active"},
    
    # Mid-Range AMD
    {"name": "AMD Radeon RX 7800 XT", "price": 499, "vram": "16GB GDDR6", "tdp": "263W", "stream_processors": 3840, "status": "Active"},
    {"name": "AMD Radeon RX 7700 XT", "price": 449, "vram": "12GB GDDR6", "tdp": "245W", "stream_processors": 3456, "status": "Active"},
    {"name": "AMD Radeon RX 7600 XT", "price": 329, "vram": "16GB GDDR6", "tdp": "190W", "stream_processors": 2048, "status": "Active"},
    {"name": "AMD Radeon RX 7600", "price": 269, "vram": "8GB GDDR6", "tdp": "165W", "stream_processors": 2048, "status": "Active"},
    
    # Budget
    {"name": "NVIDIA GeForce RTX 3050", "price": 199, "vram": "8GB GDDR6", "tdp": "130W", "cuda_cores": 2560, "status": "Active"},
    {"name": "AMD Radeon RX 6600", "price": 179, "vram": "8GB GDDR6", "tdp": "132W", "stream_processors": 1792, "status": "Active"},
    {"name": "Intel Arc A750", "price": 249, "vram": "8GB GDDR6", "tdp": "225W", "xe_cores": 28, "status": "Active"},
]

# ========== Motherboards ==========
motherboards = [
    # High-End Intel Z790
    {"name": "ASUS ROG Maximus Z790 Hero", "price": 629, "socket": "LGA1700", "chipset": "Z790", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "MSI MEG Z790 ACE", "price": 699, "socket": "LGA1700", "chipset": "Z790", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "Gigabyte Z790 AORUS Master", "price": 549, "socket": "LGA1700", "chipset": "Z790", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "ASRock Z790 Taichi", "price": 479, "socket": "LGA1700", "chipset": "Z790", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    
    # High-End AMD X670E
    {"name": "MSI MEG X670E ACE", "price": 699, "socket": "AM5", "chipset": "X670E", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "ASUS ROG Strix X670E-E Gaming", "price": 499, "socket": "AM5", "chipset": "X670E", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "Gigabyte X670E AORUS Master", "price": 449, "socket": "AM5", "chipset": "X670E", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    
    # Mid-Range Intel B760
    {"name": "MSI MAG B760 Tomahawk WiFi", "price": 229, "socket": "LGA1700", "chipset": "B760", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "ASUS TUF Gaming B760-Plus WiFi", "price": 199, "socket": "LGA1700", "chipset": "B760", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "Gigabyte B760 DS3H DDR4", "price": 139, "socket": "LGA1700", "chipset": "B760", "ram_type": "DDR4", "max_ram": "128GB", "status": "Active"},
    
    # Mid-Range AMD B650
    {"name": "MSI MAG B650 Tomahawk WiFi", "price": 219, "socket": "AM5", "chipset": "B650", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "ASUS TUF Gaming B650-Plus WiFi", "price": 189, "socket": "AM5", "chipset": "B650", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "Gigabyte B650 AORUS Elite AX", "price": 199, "socket": "AM5", "chipset": "B650", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    
    # Budget AMD B550
    {"name": "MSI B550-A PRO", "price": 139, "socket": "AM4", "chipset": "B550", "ram_type": "DDR4", "max_ram": "128GB", "status": "Active"},
    {"name": "ASUS TUF Gaming B550-Plus", "price": 149, "socket": "AM4", "chipset": "B550", "ram_type": "DDR4", "max_ram": "128GB", "status": "Active"},
]

# ========== RAM ==========
ram = [
    # High-End DDR5
    {"name": "G.Skill Trident Z5 RGB 64GB (2x32GB) DDR5-6400", "price": 259, "capacity": "64GB", "type": "DDR5", "speed": "6400 MHz", "status": "Active"},
    {"name": "Corsair Dominator Platinum RGB 64GB (2x32GB) DDR5-6400", "price": 279, "capacity": "64GB", "type": "DDR5", "speed": "6400 MHz", "status": "Active"},
    {"name": "G.Skill Trident Z5 RGB 64GB (2x32GB) DDR5-6000", "price": 229, "capacity": "64GB", "type": "DDR5", "speed": "6000 MHz", "status": "Active"},
    {"name": "Kingston Fury Beast 64GB (2x32GB) DDR5-6000", "price": 199, "capacity": "64GB", "type": "DDR5", "speed": "6000 MHz", "status": "Active"},
    
    # Mid-Range DDR5
    {"name": "G.Skill Trident Z5 32GB (2x16GB) DDR5-6000", "price": 129, "capacity": "32GB", "type": "DDR5", "speed": "6000 MHz", "status": "Active"},
    {"name": "Corsair Vengeance RGB 32GB (2x16GB) DDR5-5600", "price": 109, "capacity": "32GB", "type": "DDR5", "speed": "5600 MHz", "status": "Active"},
    {"name": "Kingston Fury Beast 32GB (2x16GB) DDR5-5200", "price": 99, "capacity": "32GB", "type": "DDR5", "speed": "5200 MHz", "status": "Active"},
    
    # High-End DDR4
    {"name": "G.Skill Trident Z RGB 64GB (2x32GB) DDR4-3600", "price": 159, "capacity": "64GB", "type": "DDR4", "speed": "3600 MHz", "status": "Active"},
    {"name": "Corsair Vengeance RGB Pro 64GB (2x32GB) DDR4-3600", "price": 149, "capacity": "64GB", "type": "DDR4", "speed": "3600 MHz", "status": "Active"},
    
    # Mid-Range DDR4
    {"name": "Corsair Vengeance LPX 32GB (2x16GB) DDR4-3600", "price": 79, "capacity": "32GB", "type": "DDR4", "speed": "3600 MHz", "status": "Active"},
    {"name": "G.Skill Ripjaws V 32GB (2x16GB) DDR4-3200", "price": 69, "capacity": "32GB", "type": "DDR4", "speed": "3200 MHz", "status": "Active"},
    
    # Budget DDR4
    {"name": "Corsair Vengeance LPX 16GB (2x8GB) DDR4-3200", "price": 45, "capacity": "16GB", "type": "DDR4", "speed": "3200 MHz", "status": "Active"},
    {"name": "Kingston Fury Beast 16GB (2x8GB) DDR4-3200", "price": 42, "capacity": "16GB", "type": "DDR4", "speed": "3200 MHz", "status": "Active"},
]

# ========== Storage ==========
storage = [
    # High-End NVMe Gen5
    {"name": "Crucial T700 4TB NVMe SSD", "price": 549, "capacity": "4TB", "type": "NVMe SSD", "read_speed": "12400 MB/s", "write_speed": "11800 MB/s", "status": "Active"},
    {"name": "Samsung 990 PRO 4TB NVMe SSD", "price": 349, "capacity": "4TB", "type": "NVMe SSD", "read_speed": "7450 MB/s", "write_speed": "6900 MB/s", "status": "Active"},
    {"name": "Crucial T700 2TB NVMe SSD", "price": 299, "capacity": "2TB", "type": "NVMe SSD", "read_speed": "12400 MB/s", "write_speed": "11800 MB/s", "status": "Active"},
    
    # High-End NVMe Gen4
    {"name": "Samsung 990 PRO 2TB NVMe SSD", "price": 189, "capacity": "2TB", "type": "NVMe SSD", "read_speed": "7450 MB/s", "write_speed": "6900 MB/s", "status": "Active"},
    {"name": "WD Black SN850X 2TB NVMe SSD", "price": 179, "capacity": "2TB", "type": "NVMe SSD", "read_speed": "7300 MB/s", "write_speed": "6600 MB/s", "status": "Active"},
    {"name": "Corsair MP600 PRO XT 2TB NVMe SSD", "price": 169, "capacity": "2TB", "type": "NVMe SSD", "read_speed": "7100 MB/s", "write_speed": "6800 MB/s", "status": "Active"},
    
    # Mid-Range NVMe
    {"name": "Samsung 980 PRO 1TB NVMe SSD", "price": 99, "capacity": "1TB", "type": "NVMe SSD", "read_speed": "7000 MB/s", "write_speed": "5000 MB/s", "status": "Active"},
    {"name": "WD Black SN770 1TB NVMe SSD", "price": 89, "capacity": "1TB", "type": "NVMe SSD", "read_speed": "5150 MB/s", "write_speed": "4900 MB/s", "status": "Active"},
    {"name": "Kingston NV2 1TB NVMe SSD", "price": 69, "capacity": "1TB", "type": "NVMe SSD", "read_speed": "3500 MB/s", "write_speed": "2100 MB/s", "status": "Active"},
    
    # Budget NVMe
    {"name": "Crucial P3 500GB NVMe SSD", "price": 39, "capacity": "500GB", "type": "NVMe SSD", "read_speed": "3500 MB/s", "write_speed": "3000 MB/s", "status": "Active"},
    {"name": "Kingston NV2 500GB NVMe SSD", "price": 35, "capacity": "500GB", "type": "NVMe SSD", "read_speed": "3500 MB/s", "write_speed": "2100 MB/s", "status": "Active"},
    
    # SATA SSD
    {"name": "Samsung 870 EVO 2TB SATA SSD", "price": 149, "capacity": "2TB", "type": "SATA SSD", "read_speed": "560 MB/s", "write_speed": "530 MB/s", "status": "Active"},
    {"name": "Crucial MX500 1TB SATA SSD", "price": 69, "capacity": "1TB", "type": "SATA SSD", "read_speed": "560 MB/s", "write_speed": "510 MB/s", "status": "Active"},
]

# ========== PSUs ==========
psus = [
    # Ultra High-End
    {"name": "Corsair HX1500i 1500W 80+ Platinum", "price": 449, "wattage": "1500W", "efficiency": "80+ Platinum", "modular": "Fully Modular", "status": "Active"},
    {"name": "Seasonic PRIME TX-1600 1600W 80+ Titanium", "price": 599, "wattage": "1600W", "efficiency": "80+ Titanium", "modular": "Fully Modular", "status": "Active"},
    {"name": "EVGA SuperNOVA 1300 G+ 1300W 80+ Gold", "price": 299, "wattage": "1300W", "efficiency": "80+ Gold", "modular": "Fully Modular", "status": "Active"},
    
    # High-End
    {"name": "Corsair RM1000x 1000W 80+ Gold", "price": 189, "wattage": "1000W", "efficiency": "80+ Gold", "modular": "Fully Modular", "status": "Active"},
    {"name": "Seasonic PRIME TX-1000 1000W 80+ Titanium", "price": 329, "wattage": "1000W", "efficiency": "80+ Titanium", "modular": "Fully Modular", "status": "Active"},
    {"name": "be quiet! Dark Power Pro 12 1200W 80+ Titanium", "price": 369, "wattage": "1200W", "efficiency": "80+ Titanium", "modular": "Fully Modular", "status": "Active"},
    
    # Mid-Range
    {"name": "Corsair RM850x 850W 80+ Gold", "price": 139, "wattage": "850W", "efficiency": "80+ Gold", "modular": "Fully Modular", "status": "Active"},
    {"name": "MSI MAG A850GL 850W 80+ Gold", "price": 119, "wattage": "850W", "efficiency": "80+ Gold", "modular": "Fully Modular", "status": "Active"},
    {"name": "EVGA SuperNOVA 750 GT 750W 80+ Gold", "price": 99, "wattage": "750W", "efficiency": "80+ Gold", "modular": "Fully Modular", "status": "Active"},
    
    # Budget
    {"name": "Corsair CX650M 650W 80+ Bronze", "price": 69, "wattage": "650W", "efficiency": "80+ Bronze", "modular": "Semi-Modular", "status": "Active"},
    {"name": "EVGA 600 W1 600W 80+ White", "price": 49, "wattage": "600W", "efficiency": "80+ White", "modular": "Non-Modular", "status": "Active"},
]

# ========== Cases ==========
cases = [
    # High-End
    {"name": "Lian Li O11 Dynamic EVO", "price": 169, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Fractal Design Torrent", "price": 209, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Corsair 5000D Airflow", "price": 164, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "be quiet! Dark Base Pro 900", "price": 249, "form_factor": "Full Tower", "color": "Black", "status": "Active"},
    
    # Mid-Range
    {"name": "NZXT H7 Flow", "price": 129, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Fractal Design Meshify 2", "price": 139, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Corsair 4000D Airflow", "price": 104, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Lian Li Lancool 216", "price": 99, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    
    # Budget
    {"name": "NZXT H510", "price": 79, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Cooler Master MasterBox Q300L", "price": 49, "form_factor": "Micro ATX", "color": "Black", "status": "Active"},
    {"name": "Phanteks Eclipse P300A", "price": 69, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
]

# ========== Coolers ==========
coolers = [
    # High-End AIO
    {"name": "Corsair iCUE H150i Elite LCD 360mm AIO", "price": 289, "type": "Liquid Cooler", "radiator_size": "360mm", "status": "Active"},
    {"name": "NZXT Kraken Z73 360mm AIO", "price": 279, "type": "Liquid Cooler", "radiator_size": "360mm", "status": "Active"},
    {"name": "Arctic Liquid Freezer II 420mm AIO", "price": 149, "type": "Liquid Cooler", "radiator_size": "420mm", "status": "Active"},
    {"name": "Lian Li Galahad II Trinity 360mm AIO", "price": 159, "type": "Liquid Cooler", "radiator_size": "360mm", "status": "Active"},
    
    # Mid-Range AIO
    {"name": "Corsair iCUE H100i Elite 240mm AIO", "price": 139, "type": "Liquid Cooler", "radiator_size": "240mm", "status": "Active"},
    {"name": "NZXT Kraken 240 AIO", "price": 119, "type": "Liquid Cooler", "radiator_size": "240mm", "status": "Active"},
    {"name": "Arctic Liquid Freezer II 280mm AIO", "price": 109, "type": "Liquid Cooler", "radiator_size": "280mm", "status": "Active"},
    
    # High-End Air
    {"name": "Noctua NH-D15 chromax.black", "price": 119, "type": "Air Cooler", "tdp_rating": "250W", "status": "Active"},
    {"name": "be quiet! Dark Rock Pro 4", "price": 89, "type": "Air Cooler", "tdp_rating": "250W", "status": "Active"},
    {"name": "Deepcool AK620", "price": 69, "type": "Air Cooler", "tdp_rating": "260W", "status": "Active"},
    
    # Budget Air
    {"name": "Cooler Master Hyper 212 Black Edition", "price": 44, "type": "Air Cooler", "tdp_rating": "180W", "status": "Active"},
    {"name": "Arctic Freezer 34 eSports DUO", "price": 49, "type": "Air Cooler", "tdp_rating": "210W", "status": "Active"},
    {"name": "ID-COOLING SE-214-XT", "price": 29, "type": "Air Cooler", "tdp_rating": "180W", "status": "Active"},
]

# Insert components
collections = {
    'cpus': cpus,
    'gpus': gpus,
    'motherboards': motherboards,
    'ram': ram,
    'storage': storage,
    'psu': psus,
    'cases': cases,
    'coolers': coolers
}

total_added = 0
total_skipped = 0

for collection_name, components in collections.items():
    collection = db[collection_name]
    print(f"\n📦 Processing {collection_name}...")
    
    for component in components:
        # Check if component already exists
        existing = collection.find_one({"name": component['name']})
        if not existing:
            result = collection.insert_one(component)
            print(f"  ✅ Added: {component['name']} (${component['price']})")
            total_added += 1
        else:
            print(f"  ⏭️  Skipped: {component['name']} (already exists)")
            total_skipped += 1

print(f"\n{'='*60}")
print(f"🎉 Import Complete!")
print(f"{'='*60}")
print(f"✅ Added: {total_added} new components")
print(f"⏭️  Skipped: {total_skipped} existing components")
print(f"\n📊 Database Summary:")
for collection_name in collections.keys():
    count = db[collection_name].count_documents({})
    print(f"  {collection_name.upper()}: {count} total components")

print(f"\n💰 Price Range Coverage:")
print(f"  Budget: $500-$1000")
print(f"  Mid-Range: $1000-$2000")
print(f"  High-End: $2000-$4000")
print(f"  Enthusiast: $4000+")
print(f"\n🚀 Your database is now ready for all budget levels!")
print(f"   Restart your Flask app and test AI recommendations!")
