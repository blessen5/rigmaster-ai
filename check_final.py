from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
count = db.components.count_documents({})
with open('final_component_count.txt', 'w', encoding='utf-8') as f:
    f.write(str(count))
