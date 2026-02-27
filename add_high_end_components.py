"""
Add High-End Components to Database
This script adds premium PC components to enable proper budget matching for high-budget builds.
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['rigmaster']

print("🚀 Adding high-end components to database...")

# High-End CPUs
high_end_cpus = [
    {"name": "Intel Core i9-14900K", "price": 589, "socket": "LGA1700", "cores": 24, "threads": 32, "base_clock": "3.2 GHz", "boost_clock": "6.0 GHz", "tdp": "125W", "status": "Active"},
    {"name": "AMD Ryzen 9 7950X", "price": 549, "socket": "AM5", "cores": 16, "threads": 32, "base_clock": "4.5 GHz", "boost_clock": "5.7 GHz", "tdp": "170W", "status": "Active"},
    {"name": "Intel Core i9-13900K", "price": 489, "socket": "LGA1700", "cores": 24, "threads": 32, "base_clock": "3.0 GHz", "boost_clock": "5.8 GHz", "tdp": "125W", "status": "Active"},
    {"name": "AMD Ryzen 9 7900X", "price": 429, "socket": "AM5", "cores": 12, "threads": 24, "base_clock": "4.7 GHz", "boost_clock": "5.4 GHz", "tdp": "170W", "status": "Active"},
    {"name": "Intel Core i7-14700K", "price": 409, "socket": "LGA1700", "cores": 20, "threads": 28, "base_clock": "3.4 GHz", "boost_clock": "5.6 GHz", "tdp": "125W", "status": "Active"},
    {"name": "AMD Ryzen 7 7800X3D", "price": 449, "socket": "AM5", "cores": 8, "threads": 16, "base_clock": "4.2 GHz", "boost_clock": "5.0 GHz", "tdp": "120W", "status": "Active"},
]

# High-End GPUs
high_end_gpus = [
    {"name": "NVIDIA GeForce RTX 4090", "price": 1599, "vram": "24GB GDDR6X", "tdp": "450W", "cuda_cores": 16384, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4080 SUPER", "price": 999, "vram": "16GB GDDR6X", "tdp": "320W", "cuda_cores": 10240, "status": "Active"},
    {"name": "AMD Radeon RX 7900 XTX", "price": 899, "vram": "24GB GDDR6", "tdp": "355W", "stream_processors": 6144, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4070 Ti SUPER", "price": 799, "vram": "16GB GDDR6X", "tdp": "285W", "cuda_cores": 8448, "status": "Active"},
    {"name": "AMD Radeon RX 7900 XT", "price": 749, "vram": "20GB GDDR6", "tdp": "315W", "stream_processors": 5376, "status": "Active"},
    {"name": "NVIDIA GeForce RTX 4070 SUPER", "price": 599, "vram": "12GB GDDR6X", "tdp": "220W", "cuda_cores": 7168, "status": "Active"},
]

# High-End Motherboards
high_end_motherboards = [
    {"name": "ASUS ROG Maximus Z790 Hero", "price": 629, "socket": "LGA1700", "chipset": "Z790", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "MSI MEG X670E ACE", "price": 699, "socket": "AM5", "chipset": "X670E", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "ASUS ROG Strix X670E-E Gaming", "price": 499, "socket": "AM5", "chipset": "X670E", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
    {"name": "Gigabyte Z790 AORUS Master", "price": 549, "socket": "LGA1700", "chipset": "Z790", "ram_type": "DDR5", "max_ram": "128GB", "status": "Active"},
]

# High-End RAM
high_end_ram = [
    {"name": "G.Skill Trident Z5 RGB 64GB (2x32GB) DDR5-6000", "price": 229, "capacity": "64GB", "type": "DDR5", "speed": "6000 MHz", "status": "Active"},
    {"name": "Corsair Dominator Platinum RGB 64GB (2x32GB) DDR5-6400", "price": 279, "capacity": "64GB", "type": "DDR5", "speed": "6400 MHz", "status": "Active"},
    {"name": "G.Skill Trident Z5 32GB (2x16GB) DDR5-6000", "price": 129, "capacity": "32GB", "type": "DDR5", "speed": "6000 MHz", "status": "Active"},
    {"name": "Corsair Vengeance RGB 32GB (2x16GB) DDR5-5600", "price": 109, "capacity": "32GB", "type": "DDR5", "speed": "5600 MHz", "status": "Active"},
]

# High-End Storage
high_end_storage = [
    {"name": "Samsung 990 PRO 2TB NVMe SSD", "price": 189, "capacity": "2TB", "type": "NVMe SSD", "read_speed": "7450 MB/s", "write_speed": "6900 MB/s", "status": "Active"},
    {"name": "WD Black SN850X 2TB NVMe SSD", "price": 179, "capacity": "2TB", "type": "NVMe SSD", "read_speed": "7300 MB/s", "write_speed": "6600 MB/s", "status": "Active"},
    {"name": "Samsung 990 PRO 4TB NVMe SSD", "price": 349, "capacity": "4TB", "type": "NVMe SSD", "read_speed": "7450 MB/s", "write_speed": "6900 MB/s", "status": "Active"},
    {"name": "Crucial T700 2TB NVMe SSD", "price": 299, "capacity": "2TB", "type": "NVMe SSD", "read_speed": "12400 MB/s", "write_speed": "11800 MB/s", "status": "Active"},
]

# High-End PSUs
high_end_psus = [
    {"name": "Corsair HX1500i 1500W 80+ Platinum", "price": 449, "wattage": "1500W", "efficiency": "80+ Platinum", "modular": "Fully Modular", "status": "Active"},
    {"name": "EVGA SuperNOVA 1300 G+ 1300W 80+ Gold", "price": 299, "wattage": "1300W", "efficiency": "80+ Gold", "modular": "Fully Modular", "status": "Active"},
    {"name": "Corsair RM1000x 1000W 80+ Gold", "price": 189, "wattage": "1000W", "efficiency": "80+ Gold", "modular": "Fully Modular", "status": "Active"},
    {"name": "Seasonic PRIME TX-1000 1000W 80+ Titanium", "price": 329, "wattage": "1000W", "efficiency": "80+ Titanium", "modular": "Fully Modular", "status": "Active"},
]

# High-End Cases
high_end_cases = [
    {"name": "Lian Li O11 Dynamic EVO", "price": 169, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Fractal Design Torrent", "price": 209, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "Corsair 5000D Airflow", "price": 164, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
    {"name": "NZXT H7 Flow", "price": 129, "form_factor": "Mid Tower", "color": "Black", "status": "Active"},
]

# High-End Coolers
high_end_coolers = [
    {"name": "Noctua NH-D15 chromax.black", "price": 119, "type": "Air Cooler", "tdp_rating": "250W", "status": "Active"},
    {"name": "Corsair iCUE H150i Elite LCD 360mm AIO", "price": 289, "type": "Liquid Cooler", "radiator_size": "360mm", "status": "Active"},
    {"name": "NZXT Kraken Z73 360mm AIO", "price": 279, "type": "Liquid Cooler", "radiator_size": "360mm", "status": "Active"},
    {"name": "be quiet! Dark Rock Pro 4", "price": 89, "type": "Air Cooler", "tdp_rating": "250W", "status": "Active"},
]

# Insert components
collections = {
    'cpus': high_end_cpus,
    'gpus': high_end_gpus,
    'motherboards': high_end_motherboards,
    'ram': high_end_ram,
    'storage': high_end_storage,
    'psu': high_end_psus,
    'cases': high_end_cases,
    'coolers': high_end_coolers
}

total_added = 0
for collection_name, components in collections.items():
    collection = db[collection_name]
    for component in components:
        # Check if component already exists
        existing = collection.find_one({"name": component['name']})
        if not existing:
            result = collection.insert_one(component)
            print(f"✅ Added {component['name']} to {collection_name}")
            total_added += 1
        else:
            print(f"⏭️  Skipped {component['name']} (already exists)")

print(f"\n🎉 Done! Added {total_added} high-end components to database.")
print("\nYour database now has premium components for high-budget builds!")
print("Restart your Flask app and try a $2000-$5000 budget recommendation.")
