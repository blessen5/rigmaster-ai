import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def compare_collections():
    local_c = MongoClient("mongodb://127.0.0.1:27017/")
    atlas_c = MongoClient(os.getenv('MONGO_URI'))
    
    local_db = local_c['rigmaster']
    atlas_db = atlas_c['rigmaster']
    
    local_cols = local_db.list_collection_names()
    atlas_cols = atlas_db.list_collection_names()
    
    with open('col_comparison.log', 'w', encoding='utf-8') as f:
        f.write(f"Local Collections: {local_cols}\n")
        f.write(f"Atlas Collections: {atlas_cols}\n")
        
        for col in local_cols:
            local_count = local_db[col].count_documents({})
            atlas_count = atlas_db[col].count_documents({})
            f.write(f"Collection '{col}': Local={local_count}, Atlas={atlas_count}\n")

if __name__ == "__main__":
    compare_collections()
