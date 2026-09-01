"""Gerador de wordlists contextuais baseado em perfis."""
import unicodedata
from typing import List, Optional, Set

def remove_accents(text: str) -> str:
    """Remove acentos e caracteres diacríticos."""
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def generate_profile_words(
    name: str = "",
    surname: str = "",
    birth_year: str = "",
    keywords: Optional[List[str]] = None
) -> List[str]:
    """
    Gera uma lista de senhas potenciais com base em informações de perfil do alvo.
    """
    words_set: Set[str] = set()
    keywords = keywords or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    # Coleta de termos base com e sem acentos
    raw_terms = []
    if name.strip():
        raw_terms.append(name.strip())
    if surname.strip():
        raw_terms.append(surname.strip())
    for kw in keywords:
        if kw.strip():
            raw_terms.append(kw.strip())

    base_terms = []
    for t in raw_terms:
        base_terms.append(t)
        no_acc = remove_accents(t)
        if no_acc != t:
            base_terms.append(no_acc)

    # Formatações de caixa
    def get_casing(term: str) -> List[str]:
        t_no_acc = remove_accents(term)
        variants = {term.lower(), term.capitalize(), term.upper()}
        variants.add(t_no_acc.lower())
        variants.add(t_no_acc.capitalize())
        variants.add(t_no_acc.upper())
        return list(variants)

    # Variações de anos
    years = []
    if birth_year and str(birth_year).strip():
        by = str(birth_year).strip()
        years.append(by)
        if len(by) == 4:
            years.append(by[2:]) # ex: '95' para '1995'
    
    # Anos comuns adicionais
    current_years = ["2023", "2024", "2025", "2026", "123", "1234", "123456", "01"]

    separators = ["", "@", ".", "_", "-", "!", "#", "$"]

    # 1. Termos simples com variações de caixa
    for term in base_terms:
        for c in get_casing(term):
            words_set.add(c)

    # 2. Combinações nome + sobrenome
    if name.strip() and surname.strip():
        n_cases = get_casing(name.strip())
        s_cases = get_casing(surname.strip())
        for n in n_cases:
            for s in s_cases:
                for sep in separators:
                    words_set.add(f"{n}{sep}{s}")
                    words_set.add(f"{s}{sep}{n}")
        # Iniciais
        n_clean = remove_accents(name.strip())
        if n_clean:
            n_init = n_clean[0]
            for s in s_cases:
                words_set.add(f"{n_init.lower()}{s}")
                words_set.add(f"{n_init.upper()}{s}")
                words_set.add(f"{s}{n_init.lower()}")

    # 3. Termos combinados com anos e sufixos numéricos
    all_years = years + [y for y in current_years if y not in years]
    for term in list(words_set):
        for y in all_years:
            for sep in separators:
                words_set.add(f"{term}{sep}{y}")
                words_set.add(f"{y}{sep}{term}")

    # 4. Termos + Símbolos comuns
    common_suffixes = ["!", "@", "#", "$", "*", "123!", "@123"]
    for w in list(words_set):
        for suf in common_suffixes:
            words_set.add(f"{w}{suf}")

    # Retorna lista ordenada e sem termos vazios
    result = [w for w in words_set if w]
    return sorted(result, key=lambda x: (len(x), x))
