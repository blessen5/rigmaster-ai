from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']

with open('indexes_outcome.txt', 'w', encoding='utf-8') as f:
    f.write("Indexes on components collection:\n")
    for name, index in db.components.index_information().items():
        f.write(f"  {name}: {index}\n")
