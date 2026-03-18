import json
import os
from bson.objectid import ObjectId

# Load sample components
base = os.path.dirname(__file__)
with open(os.path.join(base, 'component_samples.json'), 'r', encoding='utf-8') as f:
    samples = json.load(f)

# Build id -> doc mapping
id_map = {}
for cat, items in samples.items():
    for doc in items:
        _id = None
        if isinstance(doc.get('_id'), dict) and '$oid' in doc['_id']:
            _id = doc['_id']['$oid']
        elif doc.get('_id'):
            _id = str(doc['_id'])
        if _id:
            id_map[_id] = doc

class MockCollection:
    def __init__(self, id_map):
        self.id_map = id_map
    def find_one(self, query):
        qid = query.get('_id')
        if qid is None:
            return None
        # Normalize to string
        qid_str = None
        try:
            if isinstance(qid, ObjectId):
                qid_str = str(qid)
            else:
                qid_str = str(qid)
            # If representation looks like ObjectId('...'), extract
            if qid_str.startswith("ObjectId('") and qid_str.endswith("')"):
                qid_str = qid_str[len("ObjectId('"):-2]
        except Exception:
            qid_str = str(qid)
        # direct match
        if qid_str in self.id_map:
            return self.id_map[qid_str]
        # sometimes stored as plain string without $oid
        for k,v in self.id_map.items():
            if k == qid_str:
                return v
        return None

class MockDB:
    def __init__(self, id_map):
        self.components = MockCollection(id_map)

# Inject mock into app and run tests
import app
app.db = MockDB(id_map)

scenarios = [
    ('Valid AM5 Build', {
        'cpu_id': '69a186c10046746ecdf657a4',
        'motherboard_id': '69a186a50046746ecdf63614',
        'ram_id': '69a1869d0046746ecdf62833',
        'gpu_id': '69a186b40046746ecdf64974',
        'psu_id': '69a186da0046746ecdf6751b',
        'case_id': '69a186cb0046746ecdf66497',
        'storage_id': '69a186e10046746ecdf67d73'
    }),
    ('Socket Mismatch (Intel CPU on AMD Board)', {
        'cpu_id': '69a186c10046746ecdf657c7',
        'motherboard_id': '69a186a50046746ecdf63614',
        'ram_id': '69a1869d0046746ecdf62833'
    }),
]

for name, data in scenarios:
    print('\n---', name, '---')
    res = app.run_validation_logic(data)
    print('Status:', res.get('status'))
    for m in res.get('messages', []):
        print('-', m)

# Also test power analysis if available
try:
    print('\n--- Power Analysis Test ---')
    pa = app.run_power_analysis({'gpu_id': '69a186b40046746ecdf64974', 'psu_id': '69a186da0046746ecdf6751b'})
    print(pa)
except Exception as e:
    print('Power analysis error:', e)
