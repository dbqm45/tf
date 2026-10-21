# Publiczne API fabryki i zasady wersjonowania

Fabryka to **rdzeń** (`core/`) i **nakładki** (`packs/pack-*`). Rdzeń jest wersjonowany zgodnie z **Semantic
Versioning 2.0.0** (semver.org): numer w `core/factory/VERSION` (w projekcie `factory/VERSION`), historia zmian
w `core/factory/CHANGELOG.md`. Każda nakładka ma własną wersję (`version` w `pack.yaml`) i deklaruje zakres wersji
rdzenia, z którym działa (`requires.core`, np. `">=3.0.0 <4.0.0"`). Ten plik określa, co jest publicznym API rdzenia,
czyli co obiecujemy zachować w obrębie tej samej wersji MAJOR — także wobec nakładek.

## Co należy do publicznego API
| Obszar | Przykłady |
|---|---|
| nazwy skilli rdzenia i ich obecność | `core-grounding`, `core-project-record` — usunięcie albo zmiana nazwy psuje odwołania w personach, rolach, nakładkach i skillach projektu |
| format nakładki (`pack.yaml`) | klucze `id`, `version`, `title`, `description`, `content_language`, `language`, `default`, `requires` (`core`, `packs`), `optional_packs`, `facets`, `vocabulary`, `skill_requires`, `always_skills`, `standalone_skills`, `unversioned_skills`, `reference_sections`, `freshness`, `skill_visibility`, `shared_agents` (z `only_for`, `main_only`, `grounding`), `consultants`, `routing`, `routing_notes`, `contributes` (`personas`, `roles`, `agents`), `contributes_when`; pliki nakładki `roles/`, `personas/`, `traits/`, `skills/`, `hooks/`, `tests/`, `settings.json`, `cleanroom.json`, `technologies.json` |
| agenci rdzenia i znaczniki | agenci wspólni (`scout`, `quick-fixer`, `researcher`, `architect`, `security-reviewer`, `scope-reviewer`, `specialist`, `specialist-deep`), agent sesji głównej `talos`, znacznik `@dispatcher` w `only_for` i pole persony `dispatcher: true` |
| polecenia i ich flagi | `tf` (install, update, add, remove, list, language, commit-language, doctor), `factory/build.py`, `install.py`, `update.py`, `packs.py`, `migrations.py`, `profile.py`, `skill_gate.py`, `skill_audit.py`, `freshness.py`, `feedback_report.py`, `cost_stats.py`, `check.py`, `finish.py`, `facts.py`, `cost_report.py`, `run_report.py`, `hint_report.py`, `jev_calibration.py`; udokumentowane polecenia skryptów w `.claude/hooks/` i `.claude/skills/*/scripts/` |
| zmienne środowiskowe | `TEAM_FACTORY`, `TF_REPO`, `CLAUDE_SKILL_HINT*`, `CLAUDE_CONTEXT_WARN_K`, `CLAUDE_SKILL_GATE`, `CLAUDE_TDD*`, `CLAUDE_CLEANROOM_DISABLE`, `CLAUDE_JEV_*`, `TYPESAFE_*` |
| reguły blokujące hooków | co hook blokuje domyślnie: `guard_bash`, `guard_paths`, `cleanroom_guard`, `tdd_guard`, `scan_secrets` — nowa lub ostrzejsza blokada włączona domyślnie zmienia to, co wcześniej działało |
| konfiguracja użytkownika | klucze `factory/config.yaml` (tiers, profiles, routing, routing_notes, always_skills, standalone_skills, freshness, languages, default_language, default_commit_language, prices_usd_per_mtok, prices_checked, limits…; klucz manifestu `skill_overrides`, `packs`), ustawienia projektu `.claude/factory-settings.json` (`language`, `commit_language`, `targets`), schemat plików person, ról i cech; frontmatter skilli (`metadata.katalog`, `metadata.slowa`, `metadata.widocznosc`, `metadata.przeglad`) |
| układ instalacji w projekcie | ścieżki: `.claude/skills/`, `.claude/hooks/`, `.claude/agents/_generated/`, `.claude/tests/`, `factory/`, `factory/packs/<id>/`, `docs/project/`, pliki `CLAUDE.local.md`, `.claude/settings.local.json`, znaczniki `team-factory:begin`/`end` |
| formaty danych | artefakty `docs/project/` (TL;DR, Przekazanie, status), punkt kontrolny `docs/project/wip/`, plik pytań między personami `docs/project/questions.md`, scenariusze `skill_evals/*.json`, rejestr bramki (`.claude/tests/skill_gate/<id>.json`, `.claude/skill-gate.json`), logi `.claude/logs/*.jsonl`, katalog przebiegu Talosa `.claude/runs/<data>-<slug>/` (`run.json`, `story.md`, `plan.md`, `parked.md`, `report.md`) |

Nazwy skilli, person i agentów **nakładki** są publicznym API tej nakładki (wersja w jej `pack.yaml`).

**Nie** należą do publicznego API:
- treść i sformułowania skilli, promptów i cech, jeśli zachowują swój zakres;
- wewnętrzne funkcje skryptów;
- progi heurystyk (np. hooka skill_hint);
- domyślne modele tierów, które można przestawić profilem.

Zmiana zachowania widoczna dla człowieka (np. inna kolejność kroków w skillu) jest opisywana w CHANGELOG, ale nie
wymaga MAJOR.

## Które podbicie
| Zmiana | Wersja |
|---|---|
| usunięcie lub zmiana nazwy skilla, persony, agenta, polecenia, flagi, zmiennej, klucza konfiguracji lub klucza `pack.yaml`; zmiana układu instalacji lub formatu danych, która wymaga działania użytkownika | **MAJOR** — sekcja `### Breaking` z instrukcją migracji; zmiana nazwy dostaje wpis w `factory/migrations.py` (`RENAMES`), żeby `tf update` i `tf doctor --fix` poprawiły pliki projektu same |
| nowa lub ostrzejsza blokada hooka **włączona domyślnie** | **MAJOR** — w sekcji `### Breaking` także sposób przywrócenia poprzedniego zachowania |
| nowy skill, persona, polecenie, flaga, zmienna, klucz; nowa blokada **wyłączona domyślnie**; oznaczenie czegoś jako przestarzałego (zostaje jako alias) | **MINOR** — sekcje `### Added`, `### Deprecated` |
| poprawki błędów, uzupełnienie wiedzy w skillu bez zmiany zakresu, dokumentacja, testy | **PATCH** — sekcje `### Fixed`, `### Changed` |

Wycofywanie odbywa się tak:
1. Stara nazwa działa dalej jako alias przez co najmniej jedno wydanie MINOR. Przykład: `JEV_API_KEY` →
   `TYPESAFE_API_KEY` w 1.34.0.
2. CHANGELOG ma sekcję `### Deprecated`.
3. Usunięcie następuje dopiero w MAJOR.

## Zgodność nakładek z rdzeniem (autokorekta)
- `build.py check` (także w `tf doctor`) sprawdza: zakres `requires.core` każdej nakładki, wymagane nakładki,
  nakładkę języka pracy, kolizje nazw (wymiary, agenci, persony) i odwołania do nieistniejących skilli.
- Odwołania nakładki do elementów nakładek z `optional_packs`, których nie zainstalowano, są pomijane bez błędu.
- Zmiany nazw w rdzeniu i nakładkach opisuje `factory/migrations.py`; instalator stosuje je po każdej aktualizacji
  do plików projektu (własnych person, ról, nakładek i skilli), a `tf doctor --fix` — na żądanie.
- W repozytorium fabryki `python3 tools/workspace.py refs` pilnuje, żeby rdzeń nie wymieniał elementów nakładek
  (chyba że w tej samej linii nazywa nakładkę, np. „(pack-it)”), a nakładka — tylko elementy nakładek, od których
  zależy (`requires.packs`, `optional_packs`). `python3 tools/workspace.py matrix` buduje i testuje rdzeń sam, każdą
  nakładkę osobno i wszystkie razem.

## Wydanie fabryki
Wydania są automatyczne ([docs/RELEASING.md](../../docs/RELEASING.md)):
1. Commity i tytuły PR mają format Conventional Commits; typ decyduje o podbiciu według tabeli wyżej
   (`feat` → MINOR, `fix`/`perf` → PATCH, `!` lub `BREAKING CHANGE:` → MAJOR).
2. Po merge do `main` workflow `release` liczy numer (`semver.py`), zapisuje `core/factory/VERSION` i wpis
   `## [X.Y.Z] — RRRR-MM-DD` w CHANGELOG, commituje `chore(release): X.Y.Z`, tworzy tag `vX.Y.Z` i GitHub Release.
3. `python3 factory/build.py check` (w zestawionym projekcie, `tools/workspace.py check`) sprawdza:
   - poprawność wersji;
   - kolejność wpisów;
   - zgodność VERSION z CHANGELOG;
   - od 3.0.0: zgodność rodzaju podbicia z sekcjami wpisu (wcześniej od 1.35.0 w claude-team-factory).

   To samo robią workflow `factory-checks` i `release` przed commitem wydania.
4. Ręczne wydanie (`python3 scripts/release.py minor|major|patch|X.Y.Z` w PR `chore(release): X.Y.Z`) służy tylko do
   nadpisania wyniku z commitów, np. żeby dopisać sekcję `### Deprecated`.
5. Wydanej wersji nie zmieniasz. Poprawka to nowa wersja PATCH.

`update.py` porównuje wersje według precedencji SemVer, także z wersjami przedpremierowymi (`1.36.0-rc.1 < 1.36.0`),
a przy wydaniu MAJOR ostrzega i wskazuje sekcje `### Breaking` (w starszych wpisach: „Niezgodne”).

## Historia
Wersje do 2.45.0 to historia claude-team-factory, z której wydzielono rdzeń. Wersje 1.0.0–1.34.0 wydano przed
wprowadzeniem kontroli rodzaju podbicia. Trzy wydania PATCH (1.28.1, 1.29.2, 1.29.3) miały
sekcję „Nowe”, ale dodawały wyniki ewaluacji i dokumentację, a nie nowe API. Zgodnie z regułą 3 SemVer wydanych
wersji nie zmieniamy.
