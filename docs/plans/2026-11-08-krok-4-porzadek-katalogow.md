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
4a → 4b → plan 4c z decyzjami D2, D3 (także bez migracji — świeża instalacja).
