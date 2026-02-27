from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URI)
db = client['rigmaster']
components = db['components']

new_components = [
    # MONITORS
    {'name': 'MSI MAG 274QRF-QD E2', 'category': 'monitor', 'brand': 'MSI', 'status': 'Active', 'price': 349, 'specs': '27", 1440p, 180Hz, Quantum Dot'},
    {'name': 'Gigabyte M27Q-P', 'category': 'monitor', 'brand': 'Gigabyte', 'status': 'Active', 'price': 299, 'specs': '27", 1440p, 170Hz, KVM Switch'},
    {'name': 'LG 27GP950-B', 'category': 'monitor', 'brand': 'LG', 'status': 'Active', 'price': 799, 'specs': '27", 4K, 144Hz, HDMI 2.1'},
    {'name': 'Samsung Odyssey G9 G95C', 'category': 'monitor', 'brand': 'Samsung', 'status': 'Active', 'price': 1199, 'specs': '49", 5120x1440, 240Hz, VA Curved'},
    {'name': 'ASUS ProArt PA329C', 'category': 'monitor', 'brand': 'ASUS', 'status': 'Active', 'price': 1049, 'specs': '32", 4K, HDR600, 100% Adobe RGB'},
    {'name': 'ViewSonic Omni VX2728J', 'category': 'monitor', 'brand': 'ViewSonic', 'status': 'Active', 'price': 169, 'specs': '27", 1080p, 165Hz, IPS'},
    {'name': 'AOC C24G1A', 'category': 'monitor', 'brand': 'AOC', 'status': 'Active', 'price': 149, 'specs': '24", 1080p, 165Hz, Curved'},
    {'name': 'Sceptre E248W-19203R', 'category': 'monitor', 'brand': 'Sceptre', 'status': 'Active', 'price': 99, 'specs': '24", 1080p, 75Hz, Budget'},
    {'name': 'BenQ Mobiuz EX3415R', 'category': 'monitor', 'brand': 'BenQ', 'status': 'Active', 'price': 649, 'specs': '34", Ultrawide, 144Hz, IPS'},
    {'name': 'Gigabyte G34WQC A', 'category': 'monitor', 'brand': 'Gigabyte', 'status': 'Active', 'price': 369, 'specs': '34", Ultrawide, 144Hz, VA'},
    
    # PERIPHERALS
    {'name': 'Keychron Q1 Pro', 'category': 'peripherals', 'brand': 'Keychron', 'status': 'Active', 'price': 199, 'specs': '75% Wireless Mechanical Keyboard'},
    {'name': 'Ducky One 3 TKL', 'category': 'peripherals', 'brand': 'Ducky', 'status': 'Active', 'price': 124, 'specs': 'Mechanical Keyboard, Hot-swap'},
    {'name': 'EPOMAKER TH80 Pro', 'category': 'peripherals', 'brand': 'EPOMAKER', 'status': 'Active', 'price': 89, 'specs': '75% Gasket Keyboard, RGB'},
    {'name': 'Glorious Model O 2 Wireless', 'category': 'peripherals', 'brand': 'Glorious', 'status': 'Active', 'price': 99, 'specs': 'Wireless Mouse, 68g, Honeycomb'},
    {'name': 'HyperX Pulsefire Haste 2', 'category': 'peripherals', 'brand': 'HyperX', 'status': 'Active', 'price': 59, 'specs': 'Ultra-lightweight Mouse, 53g'},
    {'name': 'Finalmouse UltralightX', 'category': 'peripherals', 'brand': 'Finalmouse', 'status': 'Active', 'price': 189, 'specs': 'Carbon Fiber Mouse, 29g'},
    {'name': 'Beyerdynamic DT 770 Pro 80 Ohm', 'category': 'peripherals', 'brand': 'Beyerdynamic', 'status': 'Active', 'price': 169, 'specs': 'Studio Headphones, Closed-back'},
    {'name': 'Sennheiser HD 600', 'category': 'peripherals', 'brand': 'Sennheiser', 'status': 'Active', 'price': 349, 'specs': 'Audiophile Headphones, Open-back'},
    {'name': 'Blue Yeti Nano', 'category': 'peripherals', 'brand': 'Blue', 'status': 'Active', 'price': 99, 'specs': 'USB Microphone, Cardioid'},
    {'name': 'Elgato Stream Deck MK.2', 'category': 'peripherals', 'brand': 'Elgato', 'status': 'Active', 'price': 149, 'specs': '15 LCD Keys, Macro Pad'},
    
    # FANS
    {'name': 'Thermaltake TOUGHFAN 12', 'category': 'fans', 'brand': 'Thermaltake', 'status': 'Active', 'price': 24, 'specs': '120mm, 2000 RPM, Static Pressure'},
    {'name': 'EK-Loop FPT 120 D-RGB', 'category': 'fans', 'brand': 'EKWB', 'status': 'Active', 'price': 26, 'specs': '120mm, 2300 RPM, Daisy-Chain RGB'},
    {'name': 'Scythe Kaze Flex 120 PWM', 'category': 'fans', 'brand': 'Scythe', 'status': 'Active', 'price': 14, 'specs': '120mm, 1500 RPM, Fluid Bearing'},
    {'name': 'Cooler Master SickleFlow 120', 'category': 'fans', 'brand': 'Cooler Master', 'status': 'Active', 'price': 12, 'specs': '120mm, Rifle Bearing, Non-LED'},
    {'name': 'ID-COOLING NO-12015-XT', 'category': 'fans', 'brand': 'ID-COOLING', 'status': 'Active', 'price': 15, 'specs': '120mm Slim (15mm), 2000 RPM'},
    {'name': 'DeepCool FC120 3-in-1', 'category': 'fans', 'brand': 'DeepCool', 'status': 'Active', 'price': 49, 'specs': '3-Pack, 120mm, ARGB, Daisy-Chain'},
    
    # OS
    {'name': 'Linux Mint 22 Wilma', 'category': 'os', 'brand': 'Linux Mint', 'status': 'Active', 'price': 0, 'specs': 'Long Term Support Edition'},
    {'name': 'Arch Linux', 'category': 'os', 'brand': 'Arch', 'status': 'Active', 'price': 0, 'specs': 'Rolling Release, DIY Linux'},
    {'name': 'Windows Server 2022', 'category': 'os', 'brand': 'Microsoft', 'status': 'Active', 'price': 499, 'specs': 'Enterprise Server OS'}
]

result = components.insert_many(new_components)
print(f"{len(result.inserted_ids)} components inserted.")
client.close()
