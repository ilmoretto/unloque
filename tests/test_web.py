import unittest
import json
from unloque.web.app import create_app

class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unloque", response.data)

    def test_crack_start_missing_zip(self):
        response = self.client.post('/api/crack/start', json={})
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
