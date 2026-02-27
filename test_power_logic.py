import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Ensure we can import app
sys.path.append(os.getcwd())
from app import app

class TestPowerAnalysis(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_analyze_power_safe(self):
        """Test a scenario where PSU is sufficient"""
        # Mock DB responses
        with patch('app.db') as mock_db:
            # Setup mock find_one return values
            def side_effect(collection, query):
                # Mapping of ID to component
                cid = str(query['_id'])
                if cid == '1'*24: # CPU
                    return {'name': 'Ryzen 5 3600', 'tdp': 65}
                if cid == '2'*24: # GPU
                    return {'name': 'RTX 3060', 'tdp': 170}
                if cid == '3'*24: # RAM
                    return {'name': 'Costco RAM', 'modules': '2x8GB'}
                if cid == '4'*24: # Storage
                    return {'name': 'SSD', 'type': 'SSD'}
                if cid == '5'*24: # PSU
                    return {'name': 'Corsair RM750', 'wattage': 750}
                return None

            # We need to mock the find_one method on the collection objects
            # app.db[col].find_one(...)
            # So app.db.__getitem__ returns a mock collection, whose find_one has a side effect
            
            mock_col = MagicMock()
            mock_db.__getitem__.return_value = mock_col
            
            # We need to dispatch based on args to find_one, specifically the _id
            # But the side_effect logic above assumed direct call.
            # Let's make a router.
            
            def find_one_router(query, *args, **kwargs):
                if '_id' not in query: return None
                oid = str(query['_id'])
                if oid == '111111111111111111111111': # CPU
                    return {'name': 'Ryzen 5 3600', 'tdp': 65}
                if oid == '222222222222222222222222': # GPU
                    return {'name': 'RTX 3060', 'tdp': 170}
                if oid == '333333333333333333333333': # RAM - Fallback 10W
                    return {'name': 'RAM'}
                if oid == '444444444444444444444444': # Storage - Fallback 10W
                    return {'name': 'SSD'}
                if oid == '555555555555555555555555': # PSU
                     return {'name': 'PSU', 'wattage': 750}
                if oid == '666666666666666666666666': # Weak PSU
                     return {'name': 'Weak PSU', 'wattage': 300}
                return None

            mock_col.find_one.side_effect = find_one_router

            # Test Payload
            payload = {
                'cpu_id': '1'*24,
                'gpu_id': '2'*24,
                'ram_id': '3'*24,
                'storage_id': '4'*24,
                'psu_id': '5'*24
            }

            response = self.app.post('/api/analyze_power', 
                                   data=json.dumps(payload),
                                   content_type='application/json')
            
            data = response.get_json()
            
            print("\n--- Test 1: Safe Build ---")
            print(json.dumps(data, indent=2))
            
            # Assertions
            expected_base = 65 + 170 + 10 + 10 + 40 # = 295
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['total_base_wattage'], 295)
            self.assertTrue(data['recommended_wattage'] >= 295 * 1.3)
            self.assertEqual(data['selected_psu_wattage'], 750)
            self.assertEqual(data['adequacy_status'], 'Safe')

    def test_analyze_power_insufficient(self):
        with patch('app.db') as mock_db:
            mock_col = MagicMock()
            mock_db.__getitem__.return_value = mock_col
            
            def find_one_router(query, *args, **kwargs):
                if '_id' not in query: return None
                oid = str(query['_id'])
                if oid == '111111111111111111111111': # CPU - 65W
                    return {'name': 'Ryzen 5 3600', 'tdp': 65}
                if oid == '222222222222222222222222': # GPU - 170W
                    return {'name': 'RTX 3060', 'tdp': 170}
                # Others
                if oid == '666666666666666666666666': # Weak PSU - 250W (Below 295W)
                     return {'name': 'Weak PSU', 'wattage': 250}
                return {'name': 'Generic'} # 10W / 40W overhead logic holds

            mock_col.find_one.side_effect = find_one_router
            
            payload = {
                'cpu_id': '1'*24,
                'gpu_id': '2'*24,
                'ram_id': '3'*24, # Generic -> 10W
                'storage_id': '4'*24, # Generic -> 10W
                'psu_id': '6'*24 # Weak
            }
            
            response = self.app.post('/api/analyze_power', 
                                   data=json.dumps(payload),
                                   content_type='application/json')
            data = response.get_json()
            
            print("\n--- Test 2: Insufficient PSU ---")
            print(f"Total: {data['total_base_wattage']}, PSU: {data['selected_psu_wattage']}, Status: {data['adequacy_status']}")

            self.assertEqual(data['adequacy_status'], 'Insufficient')

if __name__ == '__main__':
    unittest.main()
