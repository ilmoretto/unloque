import unittest
import json
import io
import os
import tempfile
import pyzipper
from unloque.web.app import create_app

class TestWebApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.test_zip = os.path.join(cls.test_dir, "web_test.zip")
        with pyzipper.AESZipFile(cls.test_zip, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(b"123456")
            zf.writestr("secret.txt", b"Conteudo secreto.")

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["UPLOAD_FOLDER"] = self.test_dir
        self.client = self.app.test_client()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"UNLOQUE", response.data)
        self.assertIn(b"Recuperador", response.data)

    def test_upload_route_zip(self):
        data = {
            'file': (io.BytesIO(b"PK\x05\x06" + b"\x00"*18), 'teste.zip')
        }
        response = self.client.post('/api/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["filename"], "teste.zip")

    def test_upload_invalid_extension(self):
        data = {
            'file': (io.BytesIO(b"malware exe"), 'malware.exe')
        }
        response = self.client.post('/api/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)

    def test_audit_route(self):
        response = self.client.post('/api/audit', json={"filepath": self.test_zip})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["is_encrypted"])
        self.assertIn("files", data)

    def test_profile_generate_route(self):
        response = self.client.post('/api/profile/generate', json={
            "name": "Maria",
            "surname": "Oliveira",
            "birth_year": "2000",
            "keywords": ["financeiro"]
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total_generated"], 0)

    def test_mutate_generate_route(self):
        response = self.client.post('/api/mutate/generate', json={
            "base_words": ["admin", "root"],
            "rules": ["leetspeak", "years"]
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total_generated"], 0)

    def test_wordlists_and_examples_routes(self):
        wl_resp = self.client.get('/api/wordlists')
        self.assertEqual(wl_resp.status_code, 200)
        self.assertEqual(wl_resp.get_json()["status"], "success")

        ex_resp = self.client.get('/api/examples')
        self.assertEqual(ex_resp.status_code, 200)
        self.assertEqual(ex_resp.get_json()["status"], "success")

    def test_crack_start_missing_zip(self):
        response = self.client.post('/api/crack/start', json={})
        self.assertEqual(response.status_code, 400)

    def test_crack_flow(self):
        # Start crack with custom words
        resp = self.client.post('/api/crack/start', json={
            "zip_path": self.test_zip,
            "custom_words": ["senha1", "123456", "senha2"],
            "workers": 1
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "started")

        # Pause
        pause_resp = self.client.post('/api/crack/pause')
        self.assertEqual(pause_resp.status_code, 200)

        # Resume
        resume_resp = self.client.post('/api/crack/resume')
        self.assertEqual(resume_resp.status_code, 200)

        # Stop
        stop_resp = self.client.post('/api/crack/stop')
        self.assertEqual(stop_resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()
