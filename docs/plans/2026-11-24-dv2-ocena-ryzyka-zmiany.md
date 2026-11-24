# DV2 (część 1) — ocena ryzyka zmiany w prośbie o bramkę (mode-pdi)

**Data:** 2026-11-24 · **Źródło:** pdi `docs/plan-budowy-suity.md` §3d (DV2) · **Zależy od:** di-contract #9
(kontrakt 0.20.0: `risk` w `gate.requested`) · **Decyzja właściciela:** na razie tylko ocena — każda zmiana dalej
przechodzi przez wszystkie bramki; polityka „jaka zmiana, jakie bramki” (pytanie 12) później, na danych.

## Cel
pdi widzi przy prośbie o bramkę, jak ryzykowna jest zmiana w kodzie, z tą samą deterministyczną oceną, którą fabryka
daje w opisie PR (`tf risk`).

## Ustalenia
1. `phase_run.py gate request` liczy ocenę silnikiem `.tf/factory/risk_triage.py` (albo `$TF_RISK_TRIAGE`) względem
   domyślnej bazy `tf risk` i dokłada `risk` (`level`, `items` — najwyżej 50, `files`, `base`) do `gate.requested`.
2. Artefakty zmiany (`docs/project/`) są pomijane: na gałęzi fazy to większość różnicy, a `requirements.md` czytałby
   się jako zmieniona specyfikacja (`high`). Poziom liczony od nowa z pozostałych plików, tymi samymi regułami.
3. Bez zmian poza artefaktami (fazy B1–B3) albo bez silnika — bramka idzie bez `risk`. Ocena nigdy nie blokuje prośby.
4. Przypięcie kontraktu tf na 0.20.0.

## Kolejność (TDD)
1. Testy (czerwone) w `modes/mode-pdi/tests/test_phase_run.py`: same artefakty → bez `risk`; kod w `src/auth/` →
   `high` bez artefaktów; bez silnika → bez `risk`.
2. Kod, opis w GUIDE; bramki skilli, `check --packs mode-pdi` i `--packs all`, `refs`, `tests/test_*.py`.
