import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from bson.objectid import ObjectId

sys.path.append(os.getcwd())
try:
    from app import app
except ImportError:
    pass # Might fail if DB connection in app init fails, but mocked below

class TestCompatFix(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_am3_slash_am3_plus(self):
        """Test AM3 CPU on 'AM3+/AM3' Motherboard with Microarchitecture inference"""
        with patch('app.db') as mock_db:
             def find_one_side_effect(query, *args, **kwargs):
                if '_id' not in query: return None
                oid = str(query['_id'])
                if oid == '1'*24: # CPU: Athlon II X4 (Missing Socket, Micro: K10)
                    return {
                        '_id': ObjectId(oid), 
                        'name': 'AMD Athlon II X4 640', 
                        'socket': None,
                        'microarchitecture': 'K10' # Should infer AM3
                    }
                if oid == '2'*24: # Mobo: Gigabyte 970A (AM3+/AM3)
                    return {
                        '_id': ObjectId(oid), 
                        'name': 'Gigabyte GA-970A-DS3P', 
                        'socket_cpu': 'AM3+/AM3', 
                        'memory_type': 'DDR3'
                    }
                if oid == '3'*24: # RAM
                    return {'_id': ObjectId(oid), 'name': 'DDR3', 'type': 'DDR3'}
                return None

             mock_col = MagicMock()
             mock_col.find_one.side_effect = find_one_side_effect
             mock_db.__getitem__.return_value = mock_col
             
             payload = { 'cpu_id': '1'*24, 'motherboard_id': '2'*24, 'ram_id': '3'*24 }
             response = self.app.post('/api/validate_build', data=json.dumps(payload), content_type='application/json')
             data = response.get_json()
             
             print("\n--- Test Compat: Athlon II (Micro: K10 -> AM3) vs Mobo (AM3+/AM3) ---")
             print(f"Status: {data['status']}")
             print(f"Messages: {data['messages']}")
             
             self.assertEqual(data['status'], 'Compatible')

if __name__ == '__main__':
    unittest.main()
