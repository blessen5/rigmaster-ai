import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace db.components.find_one({'_id': ObjectId(...)}) with get_component_by_id(...)
text = re.sub(r"db\.components\.find_one\(\s*\{'_id':\s*ObjectId\(([^)]+)\)\}\s*\)", r"get_component_by_id(\1)", text)
# Handle case with multiple fields in query if any, though usually it's just _id
# Also handle db.components.find_one({'_id': ObjectId(c['_id'])}, {'name': 1})
text = re.sub(r"db\.components\.find_one\(\s*\{'_id':\s*ObjectId\(([^)]+)\)\}\s*,\s*(\{.*?\})\s*\)", r"get_component_by_id(\1)", text) # Let's just drop the projection, it's fine for get_component_by_id

# Replace db.components.find({'category': 'xxx'}) with db.xxx.find()
def replace_category_find(match):
    col = match.group(1)
    if col in ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler', 'fan', 'monitor', 'os', 'peripherals']:
        # Map to plural
        cmap = {'cpu': 'cpus', 'gpu': 'gpus', 'motherboard': 'motherboards', 'ram': 'ram', 'storage': 'storage', 
                'psu': 'psu', 'case': 'cases', 'cooler': 'coolers', 'fan': 'fans', 'monitor': 'monitors', 
                'os': 'os', 'peripherals': 'peripherals'}
        plural = cmap[col]
        return f"db.{plural}.find({{"
    return match.group(0)

# Pattern: db.components.find({'category': 'cpu', ...
# Wait, let's just use simple replaces
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'cpu'\s*,\s*", r"db.cpus.find({", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'cpu'\s*\}\)", r"db.cpus.find({})", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'gpu'\s*,\s*", r"db.gpus.find({", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'gpu'\s*\}\)", r"db.gpus.find({})", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'motherboard'\s*,\s*", r"db.motherboards.find({", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'motherboard'\s*\}\)", r"db.motherboards.find({})", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'ram'\s*,\s*", r"db.ram.find({", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'ram'\s*\}\)", r"db.ram.find({})", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'storage'\s*,\s*", r"db.storage.find({", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'storage'\s*\}\)", r"db.storage.find({})", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'psu'\s*,\s*", r"db.psu.find({", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'psu'\s*\}\)", r"db.psu.find({})", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'peripherals'\s*,\s*", r"db.peripherals.find({", text)
text = re.sub(r"db\.components\.find\(\{\s*'category'\s*:\s*'peripherals'\s*\}\)", r"db.peripherals.find({})", text)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replacement complete.")
