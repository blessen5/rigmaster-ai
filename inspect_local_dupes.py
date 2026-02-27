from pymongo import MongoClient

def inspect_local_dupes():
    c = MongoClient("mongodb://127.0.0.1:27017/")
    db = c['rigmaster']
    col = db.components
    
    pipeline = [
        {
            "$group": {
                "_id": {"name": "$name", "category": "$category"},
                "count": {"$sum": 1},
                "items": {"$push": "$$ROOT"}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}
            }
        },
        {"$limit": 5}
    ]
    
    dupes = list(col.aggregate(pipeline))
    for group in dupes:
        print(f"Group: {group['_id']} (Count: {group['count']})")
        for i, item in enumerate(group['items']):
            # Filter out big fields for readability
            print(f"  Item {i}: { {k: v for k, v in item.items() if k != '_id'} }")

if __name__ == "__main__":
    inspect_local_dupes()
