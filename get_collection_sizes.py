from pymongo import MongoClient

mongo_uri = 'mongodb+srv://rigmaster_user:MMdm2NPf8J737U8D@cluster0.99f5zmr.mongodb.net/rigmaster?retryWrites=true&w=majority&appName=Cluster0'
db_name = 'rigmaster'

output_file = 'collections_size_info.txt'

try:
    client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
    db = client[db_name]
    collections = sorted(db.list_collection_names())
    
    # Get DB stats for overall context
    db_stats = db.command("dbStats")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Database: {db_name}\n")
        f.write(f"Overall DB Size: {db_stats.get('storageSize', 0) / (1024*1024):.2f} MB\n")
        f.write(f"{'='*60}\n")
        f.write(f"{'Collection':<25} | {'Count':<10} | {'Size (KB)':<15}\n")
        f.write(f"{'-'*60}\n")
        
        for col in collections:
            stats = db.command("collStats", col)
            count = stats.get('count', 0)
            size_kb = stats.get('storageSize', 0) / 1024
            f.write(f"{col:<25} | {count:<10} | {size_kb:<15.2f}\n")
            
    print(f"Success! Size info written to {output_file}")
except Exception as e:
    print(f"Error: {e}")
