"""Cohen's κ (nominal and linearly weighted) — judge↔human agreement on a sample of tasks (N17).

Without `scipy`: we compute by hand on the stdlib. For 1–5 ratings `linear_kappa` uses linear weights
(a difference of 1 weighs less than a difference of 4), which gives a more stable signal than the nominal κ on an ordinal scale.

Source: Cohen (1960) *A coefficient of agreement for nominal scales*, educational
and psychological measurement. Built on the stdlib — the calculations are checked in the `test_flow_evals.py` tests.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence


def cohens_kappa(a: Sequence[int], b: Sequence[int]) -> float:
    """The nominal κ for two ratings of the same sample.

    κ = (p_o - p_e) / (1 - p_e), where p_o is the observed agreement, p_e the agreement expected from the marginal distributions.
    Returns 1.0 for full agreement, 0.0 for chance agreement, <0 for worse than chance.
    """
    if len(a) != len(b):
        raise ValueError(f"lengths differ: {len(a)} ≠ {len(b)}")
    if not a:
        raise ValueError("empty sample — κ undefined")
    n = len(a)
    p_o = sum(1 for x, y in zip(a, b) if x == y) / n
    ca = Counter(a)
    cb = Counter(b)
    p_e = sum((ca[k] / n) * (cb[k] / n) for k in set(a) | set(b))
    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1.0 - p_e)


def linear_kappa(a: Sequence[int], b: Sequence[int], *, levels: int = 5) -> float:
    """A weighted κ with linear weights for a 1..levels scale. Weights: w_ij = 1 - |i-j|/(levels-1).

    For a 1–5 scale a difference of 1 → weight 0.75, a difference of 2 → 0.5, …, a difference of 4 → 0. It gives a more sensitive measure
    of agreement on a rating scale (judge↔human) than the nominal κ.
    """
    if len(a) != len(b):
        raise ValueError(f"lengths differ: {len(a)} ≠ {len(b)}")
    if not a:
        raise ValueError("empty sample — κ undefined")
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
