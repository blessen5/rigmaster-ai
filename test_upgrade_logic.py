import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from bson.objectid import ObjectId

sys.path.append(os.getcwd())
from app import app

class TestUpgradeLogic(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_upgrade_readiness_basic(self):
        """Test a high-readiness build (lots of slots and headroom)"""
        with patch('app.db') as mock_db:
            def find_one_side_effect(query, *args, **kwargs):
                oid = str(query['_id'])
                if oid == '1'*24: # CPU: Ryzen 5 5600
                    return {'_id': ObjectId(oid), 'name': 'AMD Ryzen 5 5601', 'socket': 'AM4', 'tdp': 65}
                if oid == '2'*24: # Mobo: B450 (4 slots, max 64GB)
                    return {'_id': ObjectId(oid), 'name': 'Generic B450', 'memory_slots': 4, 'max_memory': 64}
                if oid == '3'*24: # RAM: 2x8GB
                    return {'_id': ObjectId(oid), 'name': '2 x 8GB DDR4'}
                if oid == '4'*24: # GPU: GTX 1660
                    return {'_id': ObjectId(oid), 'name': 'GTX 1660', 'tdp': 120}
                if oid == '5'*24: # PSU: 750W
                    return {'_id': ObjectId(oid), 'name': '750W PSU', 'wattage': 750}
                if oid == '6'*24: # Storage: NVMe
                    return {'_id': ObjectId(oid), 'name': 'NVMe SSD'}
                return None

            mock_col = MagicMock()
            mock_col.find_one.side_effect = find_one_side_effect
            mock_db.__getitem__.return_value = mock_col
            
            payload = {
                'cpu_id': '1'*24,
                'motherboard_id': '2'*24,
                'ram_id': '3'*24,
                'gpu_id': '4'*24,
                'psu_id': '5'*24,
                'storage_id': '6'*24
            }
            
            response = self.app.post('/api/analyze_upgrade', 
                                   data=json.dumps(payload),
                                   content_type='application/json')
            
            data = response.get_json()
            print("\n--- Test Upgrade Readiness: Ryzen 5 + 750W ---")
            print(json.dumps(data, indent=2))
            
            self.assertEqual(data['ram']['status'], 'Ready')
            self.assertEqual(data['gpu']['status'], 'Ready') # 750 - (65+120+50) = 515W headroom
            self.assertEqual(data['cpu']['status'], 'Ready') # AM4 non-9 tier

    def test_upgrade_readiness_maxed(self):
        """Test a low-readiness build (maxed slots, low headroom)"""
        with patch('app.db') as mock_db:
            def find_one_side_effect(query, *args, **kwargs):
                oid = str(query['_id'])
                if oid == '1'*24: # CPU: 5950X
                    return {'_id': ObjectId(oid), 'name': 'AMD Ryzen 9 5950X', 'socket': 'AM4', 'tdp': 105}
                if oid == '2'*24: # Mobo: B450 (2 slots)
                    return {'_id': ObjectId(oid), 'name': 'Cheap B450 ITX', 'memory_slots': 2}
                if oid == '3'*24: # RAM: 2x16GB
                    return {'_id': ObjectId(oid), 'name': '2 x 16GB'}
                if oid == '4'*24: # GPU: RTX 3090
                    return {'_id': ObjectId(oid), 'name': 'RTX 3090', 'tdp': 350}
                if oid == '5'*24: # PSU: 500W
                    return {'_id': ObjectId(oid), 'name': '500W PSU', 'wattage': 500}
                if oid == '6'*24: # Storage: SATA
                    return {'_id': ObjectId(oid), 'name': 'SATA SSD'}
                return None

            mock_col = MagicMock()
            mock_col.find_one.side_effect = find_one_side_effect
            mock_db.__getitem__.return_value = mock_col
            
            payload = {
                'cpu_id': '1'*24,
                'motherboard_id': '2'*24,
                'ram_id': '3'*24,
                'gpu_id': '4'*24,
                'psu_id': '5'*24,
                'storage_id': '6'*24
            }
            
            response = self.app.post('/api/analyze_upgrade', 
                                   data=json.dumps(payload),
                                   content_type='application/json')
            
            data = response.get_json()
            print("\n--- Test Upgrade Readiness: Maxed Out ITX ---")
            print(json.dumps(data, indent=2))
            
            self.assertEqual(data['ram']['status'], 'Limited') # 2/2 slots
            self.assertEqual(data['gpu']['status'], 'Not Recommended') # 500 - (105+350+50) = -5W
            self.assertEqual(data['cpu']['status'], 'Limited') # Top tier AM4

if __name__ == '__main__':
    unittest.main()
