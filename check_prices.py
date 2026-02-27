from pymongo import MongoClient
import os

def check_prices():
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(MONGO_URI)
    db = client['rigmaster']
    
    cols = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']
    
    with open("price_check_out.txt", "w") as f:
        f.write(f"{'Collection':<15} | {'Total':<6} | {'Has Price':<10} | {'Sample Price'}\n")
        f.write("-" * 50 + "\n")
        
        for col in cols:
            total = db[col].count_documents({})
            has_price = db[col].count_documents({'price': {'$exists': True}})
            
            sample = db[col].find_one({'price': {'$exists': True}})
            price_val = sample.get('price') if sample else "N/A"
            
            f.write(f"{col:<15} | {total:<6} | {has_price:<10} | {price_val}\n")

if __name__ == "__main__":
    check_prices()
