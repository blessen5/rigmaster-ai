from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

print("\nChecking unified components collection:")
count = db.components.count_documents({})
print(f"Total components: {count}")

categories = db.components.distinct('category')
print(f"Categories: {categories}")

for cat in categories:
    cat_count = db.components.count_documents({'category': cat})
    print(f"  {cat}: {cat_count}")
    
sample_gpu = db.components.find_one({'category': 'gpu'})
print(f"\nSample GPU: {sample_gpu}")
