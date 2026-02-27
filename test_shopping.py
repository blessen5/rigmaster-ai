import unittest
from unittest.mock import patch, MagicMock
from app import app
import json
from bson.objectid import ObjectId

class TestShoppingAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.db')
    def test_order_components_no_build_id(self, mock_db):
        # Mocking DB response for component lookup
        mock_db['cpus'].find_one.return_value = {'_id': ObjectId(), 'name': 'Intel Core i9-13900K'}
        mock_db.shopping_cache.find_one.return_value = None # No cache
        
        # Mocking os.getenv for SerpAPI
        with patch('os.getenv', return_value=None): # No API key, should mock
            response = self.app.post('/api/order-components', 
                                    data=json.dumps({'cpu_id': str(ObjectId())}),
                                    content_type='application/json')
            
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['status'], 'success')
            self.assertTrue(len(data['results']) > 0)
            self.assertEqual(data['results'][0]['category'], 'cpu')
            self.assertEqual(data['results'][0]['listings'][0]['source'], 'Mock Store')

    @patch('app.db')
    @patch('requests.get')
    def test_order_components_with_serpapi(self, mock_get, mock_db):
        # Mocking components
        mock_db['cpus'].find_one.return_value = {'_id': ObjectId(), 'name': 'AMD Ryzen 9 7950X'}
        mock_db.shopping_cache.find_one.return_value = None
        
        # Mocking SerpAPI response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'shopping_results': [
                {'title': 'Ryzen 9 7950X - Best Buy', 'price': '$599', 'source': 'Best Buy', 'link': 'http://example.com'}
            ]
        }
        mock_get.return_value = mock_response
        
        with patch('os.getenv', return_value='fake_key'):
            response = self.app.post('/api/order-components', 
                                    data=json.dumps({'cpu_id': str(ObjectId())}),
                                    content_type='application/json')
            
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['results'][0]['listings'][0]['source'], 'Best Buy')

if __name__ == '__main__':
    unittest.main()
