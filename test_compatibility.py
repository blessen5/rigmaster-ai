import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

sys.path.append(os.getcwd())
from app import app

class TestCompatibility(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_cpu_socket_inference(self):
        """Test if CPU socket is inferred correctly from name when DB field is missing"""
        with patch('app.db') as mock_db:
            
            # Mock find_one logic
            def find_one_side_effect(query, *args, **kwargs):
                oid = str(query['_id'])
                if oid == '1'*24: # CPU: Athlon II X4 640 (Missing Socket)
                    return {'_id': ObjectId(oid), 'name': 'AMD Athlon II X4 640 Processor', 'socket': None}
                if oid == '2'*24: # Mobo: M5A78L-M (AM3+)
                    return {'_id': ObjectId(oid), 'name': 'Asus M5A78L-M LX3', 'socket_cpu': 'AM3+', 'memory_type': 'DDR3'}
                if oid == '3'*24: # RAM
                    return {'_id': ObjectId(oid), 'name': 'DDR3 1600MHz', 'type': 'DDR3'}
                return None

            mock_col = MagicMock()
            mock_col.find_one.side_effect = find_one_side_effect
            mock_db.__getitem__.return_value = mock_col
            
            payload = {
                'cpu_id': '1'*24,
                'motherboard_id': '2'*24,
                'ram_id': '3'*24
            }
            
            response = self.app.post('/api/validate_build', 
                                   data=json.dumps(payload),
                                   content_type='application/json')
            
            data = response.get_json()
            print("\n--- Test Compatibility: Athlon II (AM3) vs AM3+ Mobo ---")
            print(json.dumps(data, indent=2))
            
            # AM3 CPU should fit in AM3+ Mobo
            self.assertEqual(data['status'], 'Compatible')

    def test_incompatible(self):
        """Test Incompatible case"""
        with patch('app.db') as mock_db:
             def find_one_side_effect(query, *args, **kwargs):
                oid = str(query['_id'])
                if oid == '1'*24: # CPU: Ryzen 5 3600 (AM4)
                    return {'_id': ObjectId(oid), 'name': 'AMD Ryzen 5 3600', 'socket': None} # Let it infer AM4
                if oid == '2'*24: # Mobo: Z490 (LGA1200)
                    return {'_id': ObjectId(oid), 'name': 'MSI Z490', 'socket': 'LGA1200', 'memory_type': 'DDR4'}
                if oid == '3'*24: # RAM
                    return {'_id': ObjectId(oid), 'name': 'DDR4', 'type': 'DDR4'}
                return None

             mock_col = MagicMock()
             mock_col.find_one.side_effect = find_one_side_effect
             mock_db.__getitem__.return_value = mock_col
             
             payload = { 'cpu_id': '1'*24, 'motherboard_id': '2'*24, 'ram_id': '3'*24 }
             response = self.app.post('/api/validate_build', data=json.dumps(payload), content_type='application/json')
             data = response.get_json()
             
             print("\n--- Test Compatibility: Ryzen (AM4) vs Z490 (LGA1200) ---")
             print(data['status'])
             
             self.assertEqual(data['status'], 'Not Compatible')

if __name__ == '__main__':
    unittest.main()
