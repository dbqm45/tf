# Plan: kopie kontraktu pdi generowane z tagu wydania i sprawdzane w CI (F2, eksport rekonstrukcji w kontrakcie)

Data: 2026-10-27 · Status: zrobione (kroki 1–5), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: decyzja właściciela 2026-10-27 — kontrakt ma jedno źródło (pdi), konsumenci trzymają przypięte, generowane
kopie sprawdzane w CI; pdi `docs/plan-f2-kontrakt-rekonstrukcja-i-wydania.md` (kontrakt 0.8.0: `reconstruction.schema.json`,
tag `contract-v<wersja>`).

## TL;DR
`tools/pdi-contract.json` przypina wersję kontraktu i mówi, który plik z `contract/` ląduje gdzie w tf.
`tools/sync_contract.py sync` pobiera pliki z tagu `contract-v<wersja>` w dbqm45/pdi (albo z katalogu `--source`)
i zapisuje kopie; `check` porównuje bajt w bajt i kończy się kodem 1 z listą rozjazdów. CI (job `repo`) uruchamia
`check`. Schemat eksportu rekonstrukcji (`eng-codebase-mapping/scripts/reconstruction-export.schema.json`) staje się
kopią `contract/reconstruction.schema.json`; pozostałe kopie (mode-pdi) przechodzą na 0.8.0.

## Decyzje
- **Bez sieci w testach:** testy skryptu używają `--source` z katalogiem tymczasowym; sieć tylko w `check` w CI
  (raw.githubusercontent.com, repo publiczne, bez sekretów).
- **`VERSION` w fixtures** generuje `sync` z wersji przypięcia; testy mode-pdi wiążą stałe wersji w skryptach
  (`triage_pdi.CONTRACT`, `phase_run.CONTRACT_VERSION`) z tą wersją zamiast z liczbą wpisaną w test.
- **Nazwa pliku u konsumenta może być inna** niż w kontrakcie (rekonstrukcja zostaje pod dotychczasową nazwą — skrypt,
  skill i ci_for_sdlc jej używają).
- **Stałe wersji w skryptach → 0.8.0:** treść zdarzeń i rekomendacji się nie zmienia; pdi sprawdza wersję wzorcem.

## Kolejność i testy
1. Czerwone testy `tests/test_sync_contract.py`: `sync` z `--source` zapisuje wszystkie miejsca i `VERSION`; `check`
   po `sync` → 0; ręczna zmiana kopii → 1 z nazwą pliku; brak pliku w źródle → 1; nieznany klucz w przypięciu → 2.
2. Kod: `tools/sync_contract.py`, `tools/pdi-contract.json`.
3. `sync --source ../pdi/contract` (kontrakt 0.8.0); testy mode-pdi: wersja z `VERSION`; stałe w skryptach.
4. CI: krok `python3 tools/sync_contract.py check` w jobie `repo`.
5. Bramki: `workspace.py check --packs mode-pdi`, `pack-it`, `all`; `refs`; testy repo; tytuł.
Kolejność wydania: najpierw PR w pdi (tag `contract-v0.8.0`), potem ten PR — `check` w CI potrzebuje tagu.
