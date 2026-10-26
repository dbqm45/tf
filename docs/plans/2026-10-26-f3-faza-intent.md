# Plan: F3 w tf — faza intent ze zgłoszenia przyjętego w pdi

Data: 2026-10-26 · Status: zrobione, PR w toku · Gałąź: `claude/f3-faza-intent`

## TL;DR
F3 w pdi (dbqm45/pdi#23): triaż `accepted` nadaje `CHG-n` i uruchamia w repo produktu fazę `intent` przez
`workflow_dispatch` szablonu `sdlc-phase.yml` z dwoma nowymi wejściami: `source` (PRB-n) i `problem` (JSON: tytuł,
rodzaj, kto, czego nie może, skutek, obejście, jak często, pomysł zgłaszającego). Ten krok dokłada w tf drugą stronę
(tryb `mode-pdi`, rdzeń bez zmian):

1. Szablon `sdlc-phase.yml`: wejścia `source` i `problem` (do poleceń tylko przez env, jak pozostałe); w fazie `intent`
   ze źródłem, gdy nie ma `docs/project/changes/CHG-n/`, krok zakłada go `decision_record.py change new CHG-n --source
   PRB-n --author pdi`.
2. `phase_run.py`: w fazie `intent` prompt niesie treść zgłoszenia z `PDI_PROBLEM` (obiekt JSON z polami
   tekstowymi; zły → błąd) i `PDI_SOURCE`, opisaną jako dane od zgłaszającego, a pomysł na rozwiązanie jako wariant do
   oceny, nie wymaganie. Inne fazy jej nie dostają.
3. SKILL.md `pdi-decisions` (punkt 5 w „Fazy uruchamiane przez pdi”, scenariusz ewaluacji przed treścią), GUIDE.md,
   `pack.yaml` 0.5.0.

## Testy (najpierw czerwone)
`test_phase_run.py`: W-2 (wejścia `source`, `problem`), W-7 (krok zakładający dziennik), I-1 (treść zgłoszenia w
prompcie fazy intent, pomysł jako nie-wymaganie), I-2 (zły `PDI_PROBLEM` → błąd), I-3 (inne fazy bez treści).

## Wynik (2026-10-26)
- Na kodzie z `main` 41/46 (czerwone W-2 ×2, W-7, I-1, I-2), po zmianie 46/46.
- Bramki: `workspace.py check --packs mode-pdi` i `--packs all`, `refs`, testy repo, `skill_gate.py pdi-decisions`
  (bez ewaluacji na modelu), `sync-gate`.
