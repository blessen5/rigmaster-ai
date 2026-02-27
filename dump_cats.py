import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
c = MongoClient('mongodb://127.0.0.1:27017/')
db = c['rigmaster']
cats = db.components.distinct("category")
with open("categories_list.txt", "w", encoding="utf-8") as f:
    f.write(", ".join(cats))
