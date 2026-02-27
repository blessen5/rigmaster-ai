from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

output = []
# Get a sample GPU from components
comp_gpu = db.components.find_one({'category': 'gpu'})
if comp_gpu:
    name = comp_gpu['name']
    comp_id = str(comp_gpu['_id'])
    
    # Try to find it in gpus collection by name
    sep_gpu = db.gpus.find_one({'name': name})
    if sep_gpu:
        sep_id = str(sep_gpu['_id'])
        output.append(f"Match found for '{name}':")
        output.append(f"  ID in 'components': {comp_id}")
        output.append(f"  ID in 'gpus':       {sep_id}")
        if comp_id == sep_id:
            output.append("  SUCCESS: IDs match.")
        else:
            output.append("  FAILURE: IDs DO NOT match!")
    else:
        output.append(f"Part '{name}' not found in 'gpus' collection.")
else:
    output.append("No GPUs found in 'components' collection.")

with open('id_check_outcome.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
