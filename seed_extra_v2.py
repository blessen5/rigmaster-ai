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
    {'name': 'MSI MPG 321URX QD-OLED', 'category': 'monitor', 'brand': 'MSI', 'status': 'Active', 'price': 1199, 'specs': '32", 4K, 240Hz, QD-OLED'},
    {'name': 'ASUS ROG Swift PG27UCDM', 'category': 'monitor', 'brand': 'ASUS', 'status': 'Active', 'price': 1299, 'specs': '27", 4K, 240Hz, QD-OLED'},
    {'name': 'MSI MPG 272QR QD-OLED', 'category': 'monitor', 'brand': 'MSI', 'status': 'Active', 'price': 899, 'specs': '27", 1440p, 500Hz, QD-OLED'},
    {'name': 'LG UltraGear 45GX990A', 'category': 'monitor', 'brand': 'LG', 'status': 'Active', 'price': 1699, 'specs': '45", 5K2K, OLED, Dual-Mode'},
    {'name': 'Alienware AW3423DWF', 'category': 'monitor', 'brand': 'Alienware', 'status': 'Active', 'price': 799, 'specs': '34", Ultrawide, 165Hz, QD-OLED'},
    {'name': 'Dell UltraSharp U3225QE', 'category': 'monitor', 'brand': 'Dell', 'status': 'Active', 'price': 969, 'specs': '32", 4K, IPS Black'},
    {'name': 'BenQ RD320U', 'category': 'monitor', 'brand': 'BenQ', 'status': 'Active', 'price': 699, 'specs': '32", 4K, IPS, Coding Mode'},
    {'name': 'Philips 27E1N1800A', 'category': 'monitor', 'brand': 'Philips', 'status': 'Active', 'price': 189, 'specs': '27", 4K, IPS'},
    {'name': 'ASUS ROG Swift PG32UCDM', 'category': 'monitor', 'brand': 'ASUS', 'status': 'Active', 'price': 1299, 'specs': '32", 4K, 240Hz, OLED'},
    {'name': 'Acer Predator XB273U', 'category': 'monitor', 'brand': 'Acer', 'status': 'Active', 'price': 449, 'specs': '27", 1440p, 240Hz'},
    
    # PERIPHERALS (Logitech, Razer, Corsair, etc.)
    {'name': 'Asus ROG Strix Scope II 96', 'category': 'peripherals', 'brand': 'ASUS', 'status': 'Active', 'price': 149, 'specs': 'Wireless Keyboard, Hall Effect'},
    {'name': 'Wooting 80HE', 'category': 'peripherals', 'brand': 'Wooting', 'status': 'Active', 'price': 199, 'specs': 'Analog Mechanical Keyboard'},
    {'name': 'Razer DeathAdder V4 Pro', 'category': 'peripherals', 'brand': 'Razer', 'status': 'Active', 'price': 149, 'specs': 'Wireless Gaming Mouse, 8K Polling'},
    {'name': 'Logitech G PRO X Superlight 2', 'category': 'peripherals', 'brand': 'Logitech', 'status': 'Active', 'price': 159, 'specs': 'Wireless Mouse, 60g, 32K Sensor'},
    {'name': 'SteelSeries Arctis Nova Elite', 'category': 'peripherals', 'brand': 'SteelSeries', 'status': 'Active', 'price': 349, 'specs': 'Wireless Headset, ANC, Hi-Res'},
    {'name': 'Audeze Maxwell', 'category': 'peripherals', 'brand': 'Audeze', 'status': 'Active', 'price': 299, 'specs': 'Wireless Planar Magnetic Headset'},
    {'name': 'Logitech G502 X Plus', 'category': 'peripherals', 'brand': 'Logitech', 'status': 'Active', 'price': 139, 'specs': 'Wireless Mouse, RGB, 13 Buttons'},
    {'name': 'Razer BlackShark V2 Pro', 'category': 'peripherals', 'brand': 'Razer', 'status': 'Active', 'price': 199, 'specs': 'Wireless Headset, THX Audio'},
    {'name': 'Corsair K100 RGB', 'category': 'peripherals', 'brand': 'Corsair', 'status': 'Active', 'price': 249, 'specs': 'Optical Gaming Keyboard'},
    {'name': 'SteelSeries Apex Pro TKL', 'category': 'peripherals', 'brand': 'SteelSeries', 'status': 'Active', 'price': 189, 'specs': 'OmniPoint Switches, OLED Screen'},
    
    # FANS
    {'name': 'Noctua NF-A12x25 G2 PWM', 'category': 'fans', 'brand': 'Noctua', 'status': 'Active', 'price': 34, 'specs': '120mm, 2000 RPM, Sterrox LCP'},
    {'name': 'Corsair iCUE LINK QX120 RGB', 'category': 'fans', 'brand': 'Corsair', 'status': 'Active', 'price': 45, 'specs': '120mm, Magnetic Dome, 2400 RPM'},
    {'name': 'Arctic P12 PWM PST Value Pack', 'category': 'fans', 'brand': 'Arctic', 'status': 'Active', 'price': 35, 'specs': '5-Pack, 120mm, 1800 RPM'},
    {'name': 'Lian Li Uni Fan SL-Infinity', 'category': 'fans', 'brand': 'Lian Li', 'status': 'Active', 'price': 29, 'specs': '120mm, Daisy-Chain, Infinity Mirror'},
    {'name': 'Be Quiet! Silent Wings Pro 4', 'category': 'fans', 'brand': 'Be Quiet!', 'status': 'Active', 'price': 32, 'specs': '120mm, 3000 RPM, High-Speed'},
    {'name': 'Noctua NF-A14 PWM chromax', 'category': 'fans', 'brand': 'Noctua', 'status': 'Active', 'price': 26, 'specs': '140mm, 1500 RPM, Silent'},
    {'name': 'Arctic P14 Max', 'category': 'fans', 'brand': 'Arctic', 'status': 'Active', 'price': 14, 'specs': '140mm, 2800 RPM, High-Performance'},
    {'name': 'Phanteks T30-120', 'category': 'fans', 'brand': 'Phanteks', 'status': 'Active', 'price': 29, 'specs': '120mm, 3000 RPM, 30mm thickness'},
    {'name': 'Cooler Master MasterFan MF120 Halo', 'category': 'fans', 'brand': 'Cooler Master', 'status': 'Active', 'price': 22, 'specs': '120mm, Dual-Loop ARGB'},
    {'name': 'NZXT F120 RGB Core', 'category': 'fans', 'brand': 'NZXT', 'status': 'Active', 'price': 24, 'specs': '120mm, Hub-Mounted RGB'},
    
    # OS
    {'name': 'Windows 11 Home (Retail)', 'category': 'os', 'brand': 'Microsoft', 'status': 'Active', 'price': 139, 'specs': 'Standard Home Edition'},
    {'name': 'Windows 11 Pro (Retail)', 'category': 'os', 'brand': 'Microsoft', 'status': 'Active', 'price': 199, 'specs': 'Pro Edition with BitLocker'},
    {'name': 'Ubuntu 24.04 LTS', 'category': 'os', 'brand': 'Canonical', 'status': 'Active', 'price': 0, 'specs': 'Open Source Desktop OS'},
    {'name': 'Windows 10 Pro (OEM)', 'category': 'os', 'brand': 'Microsoft', 'status': 'Active', 'price': 29, 'specs': 'Digital Key, Professional Edition'},
    {'name': 'Debian 12 Bookworm', 'category': 'os', 'brand': 'Debian', 'status': 'Active', 'price': 0, 'specs': 'Stable Linux Distribtion'},
    {'name': 'Fedora Workstation 40', 'category': 'os', 'brand': 'Fedora', 'status': 'Active', 'price': 0, 'specs': 'Cutting Edge Linux Desktop'}
]

result = components.insert_many(new_components)
print(f"{len(result.inserted_ids)} components inserted.")
client.close()
