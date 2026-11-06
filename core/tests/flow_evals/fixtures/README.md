# Fixtury flow-evals

Każdy katalog `fixtures/<repo>/<CHG-N>/<slug>/` jest nakładany na klon produktu przed uruchomieniem fazy
(`flow_evals_runner.apply_before`). Struktura nakładki odzwierciedla **stan zmiany PRZED** fazą do uruchomienia
(poprzedni artefakt i aktualny stan `decisions.md` — zgodnie z Z1, decyzje bramek są wiążące).

Dla `repo == "synth"` runner nie klonuje produktu — tworzy minimalny szkielet (`git init`, puste
`docs/project/changes/`) i nakłada fixturę. To ścieżka dla regresji Z1 i innych zadań niezależnych od kodu produktu.

## PR1 → PR2 (pełna wersja)

PR1 zawiera 6 fixtur minimalnych (schemat + nagłówki), żeby `--validate` przeszedł i runner nie padał na braku
plików. Prawdziwe artefakty (odpowiedzi do bramek, pełna treść `decisions.md` z A6) dojdą w PR2 po eksporcie
z `$PDI_REGISTRY_PATH/runs/` (patrz `scripts/export_pdi_runs.py` i plan N5 w `docs/plans/`).
