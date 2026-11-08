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

## 4-0 — pliki fabryki w projekcie jak `node_modules` (decyzja człowieka 2026-11-08, osobny PR przed 4a)
- Aktualizacja nadpisuje pliki fabryki zmienione w projekcie; bez `*.factory-new`, bez kopii i bez wykrywania zmian
  (zostaje `tf update --rollback` całej aktualizacji). Bez blokady edycji — reguła w `CLAUDE.md`: zmiana fabryki idzie
  przez repo fabryki.
- Wyjątek: `factory/config.yaml` to konfiguracja projektu (jak `package.json`) — ustawienia projektu zostają, nowe
  klucze najwyższego poziomu z wersji fabryki dochodzą na końcu pliku (z komentarzami). Własne pliki projektu
  (spoza manifestu) zostają nietknięte, w tym w `factory/personas/`, `roles/`, `traits/`.
- Decyzja D1 niżej przestaje obowiązywać. Wydanie MAJOR (zmiana zachowania aktualizacji), sekcja `### Breaking`.
- Testy: `tests/test_install_update.py` C-4 (nadpisanie), N-1…N-4 (konfiguracja, własne pliki, brak `*.factory-new`).

## 4a — wyniki odtwarzalne: logi, cache, przebiegi, kopie (szczegółowo)
**Decyzja człowieka 2026-11-08: bez migracji i bez okresu przejściowego.** Nowa wersja pisze i czyta wyłącznie
`.tf/`; projekt z poprzednią wersją fabryki działa po staremu, a do nowej przechodzi się świeżą instalacją (fabrykę
używa dziś tylko jej autor). Instalacja zakłada `.tf/` (jak `tf init`).

| Dziś | Po 4a | Kto pisze / czyta |
|---|---|---|
| `.claude/logs/*.jsonl`, `*.json` | `.tf/logs/` | hooki (`log_usage`, `skill_hint`, `tdd_guard`, `quality_gate`, `context_guard`, `skill_change_guard`, `jev_client`), `hint_report`, `cost_report`, `cost_stats`, `hooks_status`, `retro_data`, `update.py` (`update.jsonl`, `update-pr.md`, blokada), `skill_gate` (`evals/`) |
| `tmp/talos/runs/<przebieg>/` (i stare `.claude/runs/`) | `.tf/runs/talos/<przebieg>/` | `run_report.py`, `plan_drift.py`, `security_scan.py`, SKILL i GUIDE talosa |
| `.claude/factory-backup/` | `.tf/backup/` | `install.py` (pliki usunięte z fabryki), `update.py` (`--rollback`) |

- `.tf/` poza `.claude/` rozwiązuje też PRB-32 (Claude Code odmawia pisania do `.claude/runs/`).
- `.gitignore` / `.git/info/exclude`: instalator zamiast `.claude/logs/`, `.claude/runs/`, `tmp/talos/runs/`,
  `.claude/factory-backup/` dopisuje katalogi `.tf/` jak `tf init` (prywatna: cały `.tf/`; zespołowa: katalogi
  odtwarzalne).
- `pr_budget.py`: artefakt `.claude/runs/**` → `.tf/**`.
- Wersja: MAJOR (zmiana publicznych ścieżek logów, przebiegów i kopii), `### Breaking` z instrukcją: zainstaluj
  fabrykę na nowo.

### Testy 4a
Istniejące testy ścieżek (`test_cost`, `test_tdd`, `test_hooks_status`, `test_skill_evals`, `test_agent_retro`,
`test_auto_update`, `test_jev`, `test_run_report`, `test_plan_drift`, `test_settings_coverage`, `test_pr_budget`)
przechodzą na nowe ścieżki najpierw (czerwone), potem kod; `tools/workspace.py check` dla wszystkich przestrzeni.

### Decyzja D1 (nieaktualna — zastąpiona przez 4-0)
**D1 — pliki `*.factory-new`.** Plan nadrzędny przenosi je do `.tf/backup/`. Dziś leżą obok zmienionego pliku, bo
skill `core-factory-update` robi `diff -u plik plik.factory-new` i scala. Opcje:
- a) zostają obok pliku (tymczasowe, znikają po scaleniu; `tf update` wypisuje listę) — rekomendacja: krótka droga
  do scalenia, zero zmian w skillu aktualizacji;
- b) `.tf/backup/new/<ścieżka>` — w katalogu projektu nie ma obcych plików, ale scalenie wymaga ścieżek z dwóch
  drzew i zmiany skilla aktualizacji.

## 4b — punkt kontrolny `docs/project/wip/` → `.tf/wip/` (osobny PR, krótki plan przed kodem)
`project_record.py wip …` pisze i czyta tylko `.tf/wip/` (bez okresu przejściowego, jak 4a); skille i `CLAUDE.md` mówią „punkt kontrolny”
zamiast ścieżki tam, gdzie się da. Przed kodem: sprawdzić, czy pdi, ci_for_sdlc albo ShipScope czytają
`docs/project/wip/` (dziś `grep` w `pdi/src` i `ci_for_sdlc/packages` nic nie znajduje).

## 4c — silnik `factory/` → `.tf/factory/`, konfiguracja projektu → `.tf/config/`
Decyzje człowieka 2026-11-08: **D2** — konfiguracja projektu osobno w `.tf/config/`; **D3** — bez migracji, świeża
instalacja. Wydanie MAJOR.

**Podział (jak `node_modules` i `package.json`):**
| Gdzie | Co | Kto zmienia |
|---|---|---|
| `.tf/factory/` | cały silnik: skrypty (`build.py`, `install.py`, `update.py`, `analyze.py`…), `VERSION`, `CHANGELOG.md`, `PUBLIC_API.md`, przewodnik i FAQ, `_vendor/`, `templates/`, cechy rdzenia `traits/`, metadane nakładek `packs/<id>/`, moduły `analyzers/`, domyślna konfiguracja `config.yaml` | tylko aktualizacja (nadpisuje) |
| `.tf/config/` | `config.yaml` — **tylko nadpisania projektu**, nakładane rekurencyjnie na domyślne `.tf/factory/config.yaml` przy składaniu (słowniki łączone, inne wartości zastępowane); własne `personas/`, `roles/`, `traits/` (nadpisują te z rdzenia i nakładek o tej samej nazwie) | człowiek; instalacja zakłada pusty szablon z komentarzem, aktualizacja nie rusza |

- Skutek uboczny: znika łatanie `factory/config.yaml` przy aktualizacji (dopisywanie nowych kluczy z 4-0) — nowe klucze
  przychodzą z domyślnej konfiguracji silnika, nadpisania projektu zostają w `.tf/config/config.yaml`.
- Instalacja zespołowa: `.tf/factory/` i `.tf/config/` w gicie (jak dziś `factory/`); prywatna: cały `.tf/` poza gitem.
- Ścieżki w projekcie: `ROOT` skryptów silnika to `.tf/factory/../..`; polecenia w skillach, `CLAUDE.md`, hookach,
  regułach `permissions.allow`, szablonach CI i trybach: `python3 .tf/factory/<skrypt>.py`.
- Launcher `tf` szuka `.tf/factory/` (instalacja sprzed 9.0.0 → komunikat „zainstaluj fabrykę na nowo”).

**Zakres (sprawdzone 2026-11-08 `grep`):** ok. 100 plików — `core/factory` (25), skille rdzenia (22), testy rdzenia
(18), pack-it (11), hooki (6), przewodnik (4), tryby (6), `tools/workspace.py`, testy repo (3), `core/settings.json`,
`core/cleanroom.json`, `core/CLAUDE.md`, workflow CI; odwołania do konfiguracji: `factory/config.yaml` (40),
`factory/packs` (36), `factory/personas|roles|traits` (22).

**Kolejność w jednym PR (MAJOR):** testy na nowy układ (instalacja: `.tf/factory/`, `.tf/config/`, brak `factory/`;
składanie konfiguracji z nadpisaniami; własna persona z `.tf/config/personas/`) → `install.py` i `packs.py`/`build.py`
(układ i składanie) → `ROOT` i ścieżki w skryptach silnika → `tf.py`, `update.py`, `analyze.py` → hooki, ustawienia,
cleanroom → skille, przewodnik, `CLAUDE.md`, tryby, szablony CI → `tools/workspace.py` i testy → bramki skilli,
`workspace.py check` dla wszystkich przestrzeni (`matrix`).

## Kolejność
4a (#180) → 4b (#183) → 4c (decyzje D2, D3 z 2026-11-08).
