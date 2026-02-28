from pymongo import MongoClient
import os

MONGO_URI = 'mongodb+srv://rigmaster_user:MMdm2NPf8J737U8D@cluster0.99f5zmr.mongodb.net/rigmaster?retryWrites=true&w=majority&appName=Cluster0'

def categorize():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        db = client['rigmaster']
        print("Connected to DB")
        
        periphs = list(db.components.find({'category': 'peripherals'}))
        print(f"Total peripherals found: {len(periphs)}")
        
        counts = {'keyboard': 0, 'mouse': 0, 'headset': 0, 'webcam': 0, 'uncategorized': 0}
        
        for p in periphs:
            name = p.get('name', '').lower()
            sub_cat = None
            
            # Simple keyword matching
            if any(k in name for k in ['keyboard', 'k120', 'k70', 'rk61', 'rk62', 'huntsman', 'blackwidow', 'apex', 'strix scope', 'k100', 'k65', 'ornata', 'deathstalker', 'keychron', 'alloy core']):
                sub_cat = 'keyboard'
            elif any(k in name for k in ['mouse', 'deathadder', 'viper', 'basilisk', 'naga', 'g502', 'g pro', 'g203', 'g305', 'g703', 'g903', 'orochi', 'model o', 'model d', 'aerox', 'rival', 'sensei', 'ironclaw', 'scimitar', 'glaive', 'dark core', 'nightsword', 'katar', 'harpoon', 'm65']):
                sub_cat = 'mouse'
            elif any(k in name for k in ['headset', 'headphones', 'cloud', 'kraken', 'blackshark', 'barracuda', 'hs80', 'hs70', 'hs60', 'hs50', 'hs55', 'void', 'virtuoso', 'arctis', 'nova', 'pulse', 'stinger', 'flight']):
                sub_cat = 'headset'
            elif any(k in name for k in ['webcam', 'c920', 'c922', 'c930', 'brio', 'kiyo', 'facecam']):
                sub_cat = 'webcam'
            
            if sub_cat:
                db.components.update_one({'_id': p['_id']}, {'$set': {'sub_category': sub_cat}})
                counts[sub_cat] += 1
            else:
                counts['uncategorized'] += 1
                
        print(f"Results: {counts}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    categorize()
