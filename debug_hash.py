from pymongo import MongoClient
from werkzeug.security import check_password_hash

client = MongoClient('mongodb://localhost:27017/')
db = client['rigmaster']
user = db.users.find_one({'username': 'admin'})

with open('debug_hash.txt', 'w') as f:
    if user:
        p_hash = user['password']
        f.write(f"Hash: {p_hash}\n")
        match = check_password_hash(p_hash, 'admin123')
        f.write(f"Matches 'admin123': {match}\n")
    else:
        f.write("Admin user not found\n")
