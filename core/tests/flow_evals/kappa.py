"""Cohen's κ (nominalna i waga liniowa) — zgodność sędzia↔człowiek na próbce zadań (N17).

Bez `scipy`: liczymy ręcznie na stdlib. Przy ocenach 1–5 w `linear_kappa` używamy wag liniowych
(różnica 1 waży mniej niż różnica 4), co daje stabilniejszy sygnał niż nominalny κ na skali porządkowej.

Źródło: Cohen (1960) *A coefficient of agreement for nominal scales*, educational
and psychological measurement. Oparcie na stdlib — sprawdzone obliczenia w testach `test_flow_evals.py`.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence


def cohens_kappa(a: Sequence[int], b: Sequence[int]) -> float:
    """Nominalny κ dla dwóch ocen tej samej próbki.

    κ = (p_o - p_e) / (1 - p_e), gdzie p_o — obserwowana zgodność, p_e — oczekiwana z rozkładów brzegowych.
    Zwraca 1.0 przy pełnej zgodności, 0.0 przy przypadkowej, <0 przy gorszej niż przypadek.
    """
    if len(a) != len(b):
        raise ValueError(f"długości różne: {len(a)} ≠ {len(b)}")
    if not a:
        raise ValueError("pusta próbka — κ nieokreślony")
    n = len(a)
    p_o = sum(1 for x, y in zip(a, b) if x == y) / n
    ca = Counter(a)
    cb = Counter(b)
    p_e = sum((ca[k] / n) * (cb[k] / n) for k in set(a) | set(b))
    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1.0 - p_e)


def linear_kappa(a: Sequence[int], b: Sequence[int], *, levels: int = 5) -> float:
    """Ważony κ z wagami liniowymi dla skali 1..levels. Wagi: w_ij = 1 - |i-j|/(levels-1).

    Dla skali 1–5 różnica 1 → waga 0.75, różnica 2 → 0.5, …, różnica 4 → 0. Daje czulszy pomiar
    zgodności na skali ocen (sędzia↔człowiek) niż nominalny κ.
    """
    if len(a) != len(b):
        raise ValueError(f"długości różne: {len(a)} ≠ {len(b)}")
    if not a:
        raise ValueError("pusta próbka — κ nieokreślony")
    if levels < 2:
        raise ValueError(f"levels={levels}: potrzeba ≥ 2")
    n = len(a)
    denom = levels - 1
    p_o = sum(1.0 - abs(x - y) / denom for x, y in zip(a, b)) / n
    ca = Counter(a)
    cb = Counter(b)
    cats = sorted(set(a) | set(b))
    p_e = 0.0
    for i in cats:
        for j in cats:
            p_e += (ca[i] / n) * (cb[j] / n) * (1.0 - abs(i - j) / denom)
    if p_e >= 1.0:
        return 1.0 if p_o >= 1.0 else 0.0
    return (p_o - p_e) / (1.0 - p_e)
