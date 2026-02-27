from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
dbs = client.list_database_names()
with open('dbs_list.txt', 'w') as f:
    f.write(str(dbs))
