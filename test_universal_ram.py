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

class TestUniversalRam(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_universal_inference(self):
        """Test DDR2 and other patterns"""
        with patch('app.db') as mock_db:
             def find_one_side_effect(query, *args, **kwargs):
                if '_id' not in query: return None
                oid = str(query['_id'])
                # Reported DDR2 component
                if oid == '1'*24: 
                    return {
                        '_id': ObjectId(oid), 
                        'name': 'ADATA AD2U800B1G5-RHS 1 GB', 
                        'type': None
                    }
                # Other cases: PC3-12800
                if oid == '4'*24:
                    return {
                        '_id': ObjectId(oid), 
                        'name': 'Generic PC3-12800 Stick',
                        'type': None
                    }
                # Mobo (DDR2 / Socket 775)
                if oid == '2'*24:
                    return {
                        '_id': ObjectId(oid), 
                        'name': 'Classic LGA775 Mobo', 
                        'socket_cpu': 'LGA775' # Should infer DDR2
                    }
                # CPU (Legacy)
                if oid == '3'*24:
                    return {'_id': ObjectId(oid), 'name': 'Generic Core 2 Duo', 'microarchitecture': 'Core'}
                return None

             mock_col = MagicMock()
             mock_col.find_one.side_effect = find_one_side_effect
             mock_db.__getitem__.return_value = mock_col
             
             # Case 1: AD2 -> DDR2
             payload = { 'cpu_id': '3'*24, 'motherboard_id': '2'*24, 'ram_id': '1'*24 }
             response = self.app.post('/api/validate_build', data=json.dumps(payload), content_type='application/json')
             data = response.get_json()
             print(f"\n--- Test RAM Detection: {data['messages']}")
             self.assertEqual(data['status'], 'Compatible')
             
             # Case 2: PC3 -> DDR3 (Should NOT be compatible with LGA775 if it inferred DDR2)
             payload = { 'cpu_id': '3'*24, 'motherboard_id': '2'*24, 'ram_id': '4'*24 }
             response = self.app.post('/api/validate_build', data=json.dumps(payload), content_type='application/json')
             data = response.get_json()
             print(f"--- Test RAM Type Mismatch: {data['messages']}")
             self.assertEqual(data['status'], 'Not Compatible')

if __name__ == '__main__':
    unittest.main()
