import os
import unittest
import zipfile
import tempfile
import subprocess
from unloque.core.engine import ZipEngine, ProgressStats

class TestZipEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.matrix_zip = os.path.join(cls.test_dir, "matrix_test.zip")
        cls.plain_zip = os.path.join(cls.test_dir, "plain_test.zip")
        cls.wordlist_file = os.path.join(cls.test_dir, "wordlist.txt")

        # Criar subpasta com múltiplas wordlists
        cls.wordlists_dir = os.path.join(cls.test_dir, "wordlists_dir")
        os.makedirs(cls.wordlists_dir, exist_ok=True)
        with open(os.path.join(cls.wordlists_dir, "lista1.txt"), "w") as f:
            f.write("123456\nsenha123\n")
        with open(os.path.join(cls.wordlists_dir, "lista2.txt"), "w") as f:
            f.write("admin\nmatrix\n")

        # Criar arquivo de texto base
        txt_path = os.path.join(cls.test_dir, "file.txt")
        with open(txt_path, "w") as f:
            f.write("Conteudo secreto para teste.")

        # Criar ZIP criptografado com senha 'matrix'
        subprocess.run(["zip", "-P", "matrix", "-q", "-j", cls.matrix_zip, txt_path], check=True)

        # Criar ZIP sem senha
        with zipfile.ZipFile(cls.plain_zip, "w") as zf:
            zf.write(txt_path, arcname="file.txt")

        # Criar wordlist de teste
        with open(cls.wordlist_file, "w") as f:
            f.write("123456\npassword\nadmin\nmatrix\nqwerty\n")

    def test_single_password_success(self):
        engine = ZipEngine(self.matrix_zip)
        self.assertTrue(engine.test_password("matrix"))

    def test_single_password_failure(self):
        engine = ZipEngine(self.matrix_zip)
        self.assertFalse(engine.test_password("senha_errada"))

    def test_crack_with_file_wordlist(self):
        engine = ZipEngine(self.matrix_zip)
        result = engine.crack(self.wordlist_file, workers=2)
        self.assertTrue(result.found)
        self.assertEqual(result.password, "matrix")
        self.assertEqual(result.status, "found")

    def test_crack_with_directory(self):
        engine = ZipEngine(self.matrix_zip)
        result = engine.crack(self.wordlists_dir, workers=2)
        self.assertTrue(result.found)
        self.assertEqual(result.password, "matrix")
        self.assertEqual(result.status, "found")

    def test_crack_with_list_wordlist(self):
        engine = ZipEngine(self.matrix_zip)
        wordlist = ["teste1", "teste2", "matrix", "teste3"]
        result = engine.crack(wordlist, workers=2)
        self.assertTrue(result.found)
        self.assertEqual(result.password, "matrix")

    def test_crack_exhausted(self):
        engine = ZipEngine(self.matrix_zip)
        wordlist = ["senha1", "senha2", "senha3"]
        result = engine.crack(wordlist, workers=2)
        self.assertFalse(result.found)
        self.assertEqual(result.status, "exhausted")

    def test_plain_zip_error(self):
        with self.assertRaises(ValueError):
            ZipEngine(self.plain_zip)

    def test_generator_events(self):
        engine = ZipEngine(self.matrix_zip)
        events = list(engine.crack_generator(self.wordlist_file, workers=2, chunk_size=2))
        self.assertGreater(len(events), 0)
        last_event = events[-1]
        self.assertTrue(last_event.found)
        self.assertEqual(last_event.password, "matrix")

if __name__ == "__main__":
    unittest.main()
