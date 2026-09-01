"""Testes do gerador contextual."""
import unittest
from unloque.core.profiler import generate_profile_words

class TestProfiler(unittest.TestCase):

    def test_generate_profile_basic(self):
        words = generate_profile_words(name="João", surname="Silva", birth_year="1995")
        self.assertGreater(len(words), 0)
        self.assertIn("joao", words)
        self.assertIn("silva", words)
        self.assertTrue(any("1995" in w for w in words))

    def test_generate_profile_with_keywords(self):
        words = generate_profile_words(name="Admin", keywords=["empresa", "2024"])
        self.assertGreater(len(words), 0)
        self.assertIn("empresa", words)

if __name__ == '__main__':
    unittest.main()
