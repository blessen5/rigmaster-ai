import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from bson.objectid import ObjectId

sys.path.append(os.getcwd())
try:
    from app import app
except:
    pass

class TestRamInference(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_ram_pattern_recognition(self):
        """Test if 'AD3' in name is correctly identified as DDR3"""
        with patch('app.db') as mock_db:
             def find_one_side_effect(query, *args, **kwargs):
                if '_id' not in query: return None
                oid = str(query['_id'])
                # Reported component
                if oid == '1'*24: 
                    return {
                        '_id': ObjectId(oid), 
                        'name': 'ADATA AD3S1066B2G7-R 2 GB', 
                        'type': None, # Simulated missing/unclear type
                        'memory_type': None
                    }
                # Mobo (DDR3)
                if oid == '2'*24:
                    return {
                        '_id': ObjectId(oid), 
                        'name': 'Generic DDR3 Mobo', 
                        'memory_type': 'DDR3'
                    }
                # CPU
                if oid == '3'*24:
                    return {'_id': ObjectId(oid), 'name': 'Generic CPU', 'socket': 'AM3'}
                return None

             mock_col = MagicMock()
             mock_col.find_one.side_effect = find_one_side_effect
             mock_db.__getitem__.return_value = mock_col
             
             payload = { 
                 'cpu_id': '3'*24, 
                 'motherboard_id': '2'*24, 
                 'ram_id': '1'*24 
             }
             response = self.app.post('/api/validate_build', data=json.dumps(payload), content_type='application/json')
             data = response.get_json()
             
             print("\n--- Test RAM: AD3S1066 (Inferred DDR3) ---")
             print(f"Status: {data['status']}")
             print(f"Messages: {data['messages']}")
             
             self.assertEqual(data['status'], 'Compatible')
             self.assertFalse(any("Could not identify RAM generation" in m for m in data['messages']))

if __name__ == '__main__':
    unittest.main()
