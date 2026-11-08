# Plan kroku 4: porządek w katalogach — wyniki pracy fabryki w `.tf/`

Stan: 2026-11-08, do akceptacji. Plan nadrzędny: `docs/plans/2026-11-08-tf-analyze-i-katalog-tf.md` (sekcje 0, 1
i 7, krok 4). Krok 1 założył `.tf/` (`tf init`, `core/factory/analyze.py`); nikt poza `tf analyze` jeszcze do niego
nie pisze.

## Skala (sprawdzone 2026-11-08 `grep` po `core/`, `packs/`, `modes/`, `tools/`, `tests/`, `scripts/`, `.github/`)
| Ścieżka | Pliki | Wystąpienia |
|---|---|---|
| `factory/` | 109 | 523 |
| `.claude/logs` (dosłownie; do tego ok. 10 miejsc składa ścieżkę z `".claude"` i `"logs"`) | 24 | 34 |
| `.claude/runs` + `tmp/talos/runs` | 25 | 54 |
| `docs/project/wip` | 10 | 16 |
| `factory-backup` + `factory-new` | 20 | 64 |

Przeniesienie `factory/` to większość pracy i zmiana publicznego API (układ instalacji) — dlatego krok dzielę na
trzy osobne PR, od najmniej ryzykownego.

## 4a — wyniki odtwarzalne: logi, cache, przebiegi, kopie (ten plan, szczegółowo)
**Reguła przejścia (jedna dla wszystkich):** gdy w projekcie jest katalog `.tf/`, fabryka pisze do `.tf/<katalog>`;
bez `.tf/` — tak jak dziś. Czytający (raporty, statusy, wznawianie) czytają obie lokalizacje. Projekt, w którym nikt
nie uruchomił `tf init` ani aktualizacji, działa bez zmian.

| Dziś | Po 4a (z `.tf/`) | Kto pisze / czyta |
|---|---|---|
| `.claude/logs/*.jsonl`, `*.json` | `.tf/logs/` | hooki (`log_usage`, `skill_hint`, `tdd_guard`, `quality_gate`, `context_guard`, `skill_change_guard`, `jev_client`), `hint_report`, `cost_report`, `cost_stats`, `hooks_status`, `retro_data` |
| `.claude/cache/` | `.tf/cache/` | (1 miejsce) |
| `tmp/talos/runs/<przebieg>/` (i stare `.claude/runs/`) | `.tf/runs/talos/<przebieg>/` | `run_report.py`, `plan_drift.py`, `security_scan.py`, SKILL talosa |
| `.claude/factory-backup/` | `.tf/backup/` | `install.py`, `update.py` (`--rollback` czyta obie) |

- **Wspólna funkcja ścieżek** `core/hooks/tf_paths.py` (`state_dir(root, "logs" | "cache" | "runs" | "backup")`
  i `read_dirs(root, …)` zwracające nową i starą lokalizację). Hooki importują ją z własnego katalogu; skrypty
  w `factory/` i w skillach ładują ją z `.claude/hooks/` z zapasową kopią trzech linii, gdy hooka nie ma (skrypt
  skilla uruchomiony poza projektem).
- **`.tf/` poza `.claude/`** rozwiązuje też PRB-32: Claude Code odmawia pisania do `.claude/runs/` (lista chronionych
  ścieżek), dlatego talos przeniósł się do `tmp/talos/runs/`; `.tf/runs/` nie jest chroniony.
- **Migracja** (`core/factory/migrations.py`, przy `tf update` i `tf doctor --fix`): tworzy `.tf/` (jak `tf init`),
  przenosi zawartość `.claude/logs/`, `.claude/cache/`, `tmp/talos/runs/`, `.claude/runs/`,
  `.claude/factory-backup/` do nowych miejsc (bez nadpisywania; konflikt nazw → zostaje w starym miejscu
  i ostrzeżenie), usuwa puste stare katalogi. Świeża instalacja od razu robi `tf init`.
- **Git:** wpisy `.gitignore`/`.git/info/exclude` dla nowych katalogów robi już `tf init` (krok 1); stare wpisy
  zostają do kroku sprzątania.
- **Wersja:** MINOR (stare lokalizacje działają dalej, migracja automatyczna); wpis w CHANGELOG przez CI;
  w `PUBLIC_API.md` nowe lokalizacje z adnotacją „od X.Y.Z; wcześniej …, czytane dla zgodności”.

### Decyzja do człowieka przed 4a
**D1 — pliki `*.factory-new`.** Plan nadrzędny przenosi je do `.tf/backup/`. Dziś leżą obok zmienionego pliku, bo
skill `core-factory-update` robi `diff -u plik plik.factory-new` i scala. Opcje:
- a) zostają obok pliku (tymczasowe, znikają po scaleniu; `tf update` wypisuje listę) — rekomendacja: krótka droga
  do scalenia, zero zmian w skillu aktualizacji;
- b) `.tf/backup/new/<ścieżka>` — w katalogu projektu nie ma obcych plików, ale scalenie wymaga ścieżek z dwóch
  drzew i zmiany skilla aktualizacji.

### Testy 4a (najpierw czerwone)
- `core/tests/test_tf_paths.py`: z `.tf/` → nowa lokalizacja, bez → stara; `read_dirs` zwraca obie, istniejące.
- Hooki: z `.tf/` log ląduje w `.tf/logs/` (`test_hooks.py`, `test_cost.py`, `test_quality_gate.py` — nowe przypadki
  obok istniejących, istniejące bez zmian = dowód zgodności).
- `test_run_report.py`, `test_plan_drift.py`: przebieg w `.tf/runs/talos/` przy `.tf/`; wznawianie przebiegu
  z `tmp/talos/runs/` i `.claude/runs/`.
- `test_update.py` / migracje: przeniesienie zawartości, brak nadpisania, ostrzeżenie przy konflikcie,
  `--rollback` z kopii w `.tf/backup/` i ze starej lokalizacji.
- `tools/workspace.py check` dla wszystkich przestrzeni (`matrix`).

## 4b — punkt kontrolny `docs/project/wip/` → `.tf/wip/` (osobny PR, krótki plan przed kodem)
`project_record.py wip …` pisze do `.tf/wip/` przy `.tf/`, czyta obie; skille i `CLAUDE.md` mówią „punkt kontrolny”
zamiast ścieżki tam, gdzie się da. Przed kodem: sprawdzić, czy pdi, ci_for_sdlc albo ShipScope czytają
`docs/project/wip/` (dziś `grep` w `pdi/src` i `ci_for_sdlc/packages` nic nie znajduje).

## 4c — silnik `factory/` → `.tf/factory/` (osobny plan i decyzje przed kodem)
Zmiana układu instalacji (publiczne API rdzenia): 523 odwołania (polecenia w skillach i `CLAUDE.md`
typu `python3 factory/build.py`, hooki, launcher `tf`, `install.py`/`update.py`, testy). Przed planem:
- **D2:** co z konfiguracją użytkownika w `factory/` (`personas/`, `roles/`, `traits/`, `config.yaml`, `packs/` —
  dziś `USER_OWNED`): razem do `.tf/factory/`, czy osobno (`.tf/config/`), czy zostaje.
- **D3:** czy MAJOR z jednorazową migracją (`tf update` przenosi i poprawia odwołania przez `RENAMES`), czy okres,
  w którym `factory/` to cienka nakładka przekierowująca do `.tf/factory/`.
- Fakt do sprawdzenia w dokumentacji Claude Code: które lokalizacje pliku instrukcji są wczytywane
  (`CLAUDE.local.md` w katalogu głównym vs `.claude/`) [niezweryfikowane].

## Kolejność
4a (po decyzji D1) → 4b → plan 4c z decyzjami D2, D3.
