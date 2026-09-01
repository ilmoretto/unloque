"""Gerador de mutações e regras de transformação de senhas."""
from typing import List, Set, Optional

LEET_MAP = {
    "a": ["4", "@"],
    "e": ["3"],
    "i": ["1", "!"],
    "o": ["0"],
    "s": ["5", "$"],
    "t": ["7"],
    "b": ["8"],
    "g": ["9"]
}

def apply_leetspeak(word: str) -> Set[str]:
    """Gera variações em leetspeak para uma palavra."""
    results = {word}
    
    # Substituição direta simples
    simple_leet = word
    for char, subs in LEET_MAP.items():
        simple_leet = simple_leet.replace(char.lower(), subs[0])
        simple_leet = simple_leet.replace(char.upper(), subs[0])
    results.add(simple_leet)

    # Variações com caracteres alternativos
    for char, subs in LEET_MAP.items():
        for sub in subs:
            w_sub = word.replace(char.lower(), sub).replace(char.upper(), sub)
            results.add(w_sub)

    return results

def mutate_words(base_words: List[str], rules: Optional[List[str]] = None) -> List[str]:
    """
    Aplica regras de mutação sobre uma lista de palavras base.
    Regras disponíveis: 'leetspeak', 'years', 'suffixes', 'prefixes', 'casing', 'reverse'.
    """
    if not rules:
        rules = ["leetspeak", "years", "suffixes", "casing"]

    rules_set = {r.lower().strip() for r in rules}
    all_words: Set[str] = set()

    for raw in base_words:
        w = raw.strip()
        if not w:
            continue
        all_words.add(w)

        # Casing
        if "casing" in rules_set or "all" in rules_set:
            all_words.add(w.lower())
            all_words.add(w.upper())
            all_words.add(w.capitalize())
            all_words.add(w.swapcase())

        # Reverse
        if "reverse" in rules_set or "all" in rules_set:
            all_words.add(w[::-1])

    # Leetspeak
    if "leetspeak" in rules_set or "all" in rules_set:
        leet_generated = set()
        for w in list(all_words):
            leet_generated.update(apply_leetspeak(w))
        all_words.update(leet_generated)

    # Sufixos e Anos
    years = ["2020", "2021", "2022", "2023", "2024", "2025", "2026", "2000", "1999", "123", "1234", "123456"]
    suffixes = ["!", "@", "#", "$", "%", "*", "_", "123", "!@#", "2024!", "2025!", "2026!"]
    prefixes = ["#", "!", "@", "_", "the", "my"]

    current_pool = list(all_words)

    if "years" in rules_set or "all" in rules_set:
        for w in current_pool:
            for y in years:
                all_words.add(f"{w}{y}")
                all_words.add(f"{w}@{y}")
                all_words.add(f"{w}_{y}")

    if "suffixes" in rules_set or "all" in rules_set:
        for w in current_pool:
            for s in suffixes:
                all_words.add(f"{w}{s}")

    if "prefixes" in rules_set or "all" in rules_set:
        for w in current_pool:
            for p in prefixes:
                all_words.add(f"{p}{w}")
                all_words.add(f"{p}_{w}")

    result = [w for w in all_words if w]
    return sorted(result, key=lambda x: (len(x), x))
