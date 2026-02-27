from pymongo import MongoClient
import json

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

output = []
output.append("Checking unified components collection:")
count = db.components.count_documents({})
output.append(f"Total components: {count}")

categories = db.components.distinct('category')
output.append(f"Categories: {categories}")

for cat in categories:
    cat_count = db.components.count_documents({'category': cat})
    output.append(f"  {cat}: {cat_count}")
    
sample_gpu = db.components.find_one({'category': 'gpu'})
if sample_gpu:
    sample_gpu['_id'] = str(sample_gpu['_id'])
    output.append(f"\nSample GPU: {json.dumps(sample_gpu, indent=2)}")
else:
    output.append("\nNo GPU found with category 'gpu'")

# Check for 'gpus' plural too
sample_gpus = db.components.find_one({'category': 'gpus'})
if sample_gpus:
    sample_gpus['_id'] = str(sample_gpus['_id'])
    output.append(f"\nSample GPU (plural): {json.dumps(sample_gpus, indent=2)}")

with open('db_check_outcome.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
