"""Testes do auditor de cabeçalhos PKZIP."""
import os
import unittest
import tempfile
import pyzipper
import zipfile
from unloque.core.analyzer import analyze_zip

class TestAnalyzer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.aes_zip = os.path.join(cls.test_dir, "aes_test.zip")
        cls.plain_zip = os.path.join(cls.test_dir, "plain_test.zip")

        txt_path = os.path.join(cls.test_dir, "document.txt")
        with open(txt_path, "w") as f:
            f.write("Informação confidencial para análise.")

        # Criar ZIP AES
        with pyzipper.AESZipFile(cls.aes_zip, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(b"teste123")
            zf.write(txt_path, arcname="document.txt")

        # Criar ZIP sem senha
        with zipfile.ZipFile(cls.plain_zip, "w") as zf:
            zf.write(txt_path, arcname="document.txt")

    def test_analyze_aes_zip(self):
        result = analyze_zip(self.aes_zip)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["is_encrypted"])
        self.assertIn("AES", result["encryption_type"])
        self.assertIn("files", result)
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0]["filename"], "document.txt")
        self.assertTrue(result["files"][0]["is_encrypted"])

    def test_analyze_plain_zip(self):
        result = analyze_zip(self.plain_zip)
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["is_encrypted"])
        self.assertEqual(result["vulnerability_level"], "NONE")

    def test_analyze_non_existent(self):
        with self.assertRaises(FileNotFoundError):
            analyze_zip(os.path.join(self.test_dir, "nao_existe.zip"))

if __name__ == '__main__':
    unittest.main()
