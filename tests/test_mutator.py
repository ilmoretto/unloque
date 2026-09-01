"""Testes do gerador de mutações."""
import unittest
from unloque.core.mutator import mutate_words, apply_leetspeak

class TestMutator(unittest.TestCase):

    def test_apply_leetspeak(self):
        result = apply_leetspeak("admin")
        self.assertTrue(any("4" in w or "@" in w or "1" in w or "!" in w for w in result))

    def test_mutate_words_rules(self):
        base = ["teste"]
        mutated = mutate_words(base, rules=["leetspeak", "years", "suffixes", "casing"])
        self.assertGreater(len(mutated), 1)
        self.assertIn("TESTE", mutated)
        self.assertTrue(any("2024" in w for w in mutated))
        self.assertTrue(any("!" in w for w in mutated))

if __name__ == '__main__':
    unittest.main()
