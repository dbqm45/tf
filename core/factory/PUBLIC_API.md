# Publiczne API fabryki i zasady wersjonowania

Fabryka jest wersjonowana zgodnie z **Semantic Versioning 2.0.0** (semver.org). Numer jest w `factory/VERSION`, a historia
zmian w `factory/CHANGELOG.md`. Ten plik określa, co jest publicznym API, czyli co obiecujemy zachować w obrębie tej
samej wersji MAJOR.

## Co należy do publicznego API
| Obszar | Przykłady |
|---|---|
| nazwy skilli i ich obecność | `core-grounding`, `be-api-design` — usunięcie albo zmiana nazwy psuje odwołania w personach, rolach i skillach projektu |
| persony i agenci uruchamiani przez człowieka | `claude --agent maja`, `ewa`, `tomasz`, … oraz nazwy agentów wspólnych (`scout`, `architect`, …) |
| polecenia i ich flagi | `factory/build.py`, `install.py`, `update.py`, `profile.py`, `skill_gate.py`, `skill_audit.py`, `freshness.py`, `feedback_report.py`, `cost_stats.py`, `check.py`, `finish.py`, `facts.py`, `cost_report.py`, `hint_report.py`, `jev_calibration.py`; udokumentowane polecenia skryptów w `.claude/hooks/` i `.claude/skills/*/scripts/` |
| zmienne środowiskowe | `CLAUDE_SKILL_HINT*`, `CLAUDE_CONTEXT_WARN_K`, `CLAUDE_SKILL_GATE`, `CLAUDE_TDD*`, `CLAUDE_JEV_*`, `TYPESAFE_*` |
| reguły blokujące hooków | co hook blokuje domyślnie: `guard_bash`, `guard_paths`, `cleanroom_guard`, `tdd_guard`, `scan_secrets` — nowa lub ostrzejsza blokada włączona domyślnie zmienia to, co wcześniej działało |
| konfiguracja użytkownika | klucze `factory/config.yaml` (tiers, profiles, routing, always_skills, standalone_skills, freshness, prices_usd_per_mtok, prices_checked, limits…; klucz manifestu `skill_overrides`), schemat plików `factory/personas`, `roles`, `traits`; frontmatter skilli (`metadata.katalog`, `metadata.slowa`, `metadata.widocznosc`, `metadata.przeglad`) |
| układ instalacji w projekcie | ścieżki: `.claude/skills/`, `.claude/hooks/`, `.claude/agents/_generated/`, `.claude/tests/`, `factory/`, `docs/project/`, pliki `CLAUDE.local.md`, `.claude/settings.local.json` |
| formaty danych | artefakty `docs/project/` (TL;DR, Przekazanie, status), punkt kontrolny `docs/project/wip/`, scenariusze `skill_evals/*.json`, rejestr bramki, logi `.claude/logs/*.jsonl` |

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
| usunięcie lub zmiana nazwy skilla, persony, agenta, polecenia, flagi, zmiennej, klucza konfiguracji; zmiana układu instalacji lub formatu danych, która wymaga działania użytkownika | **MAJOR** — sekcja `### Breaking` z instrukcją migracji |
| nowa lub ostrzejsza blokada hooka **włączona domyślnie** | **MAJOR** — w sekcji `### Breaking` także sposób przywrócenia poprzedniego zachowania |
| nowy skill, persona, polecenie, flaga, zmienna, klucz; nowa blokada **wyłączona domyślnie**; oznaczenie czegoś jako przestarzałego (zostaje jako alias) | **MINOR** — sekcje `### Added`, `### Deprecated` |
| poprawki błędów, uzupełnienie wiedzy w skillu bez zmiany zakresu, dokumentacja, testy | **PATCH** — sekcje `### Fixed`, `### Changed` |

Wycofywanie odbywa się tak:
1. Stara nazwa działa dalej jako alias przez co najmniej jedno wydanie MINOR. Przykład: `JEV_API_KEY` →
   `TYPESAFE_API_KEY` w 1.34.0.
2. CHANGELOG ma sekcję `### Deprecated`.
3. Usunięcie następuje dopiero w MAJOR.

## Wydanie fabryki
Wydania są automatyczne ([docs/RELEASING.md](../docs/RELEASING.md)):
1. Commity i tytuły PR mają format Conventional Commits; typ decyduje o podbiciu według tabeli wyżej
   (`feat` → MINOR, `fix`/`perf` → PATCH, `!` lub `BREAKING CHANGE:` → MAJOR).
2. Po merge do `main` workflow `release` liczy numer (`semver.py`), zapisuje `factory/VERSION` i wpis
   `## [X.Y.Z] — RRRR-MM-DD` w CHANGELOG, commituje `chore(release): X.Y.Z`, tworzy tag `vX.Y.Z` i GitHub Release.
3. `python3 factory/build.py check` sprawdza:
   - poprawność wersji;
   - kolejność wpisów;
   - zgodność VERSION z CHANGELOG;
   - od 1.35.0: zgodność rodzaju podbicia z sekcjami wpisu.

   To samo robią workflow `factory-checks` i `release` przed commitem wydania.
4. Ręczne wydanie (`python3 scripts/release.py minor|major|patch|X.Y.Z` w PR `chore(release): X.Y.Z`) służy tylko do
   nadpisania wyniku z commitów, np. żeby dopisać sekcję `### Deprecated`.
5. Wydanej wersji nie zmieniasz. Poprawka to nowa wersja PATCH.

`update.py` porównuje wersje według precedencji SemVer, także z wersjami przedpremierowymi (`1.36.0-rc.1 < 1.36.0`),
a przy wydaniu MAJOR ostrzega i wskazuje sekcje `### Breaking` (w starszych wpisach: „Niezgodne”).

## Historia przed 1.35.0
Wersje 1.0.0–1.34.0 wydano przed wprowadzeniem tej kontroli. Trzy wydania PATCH (1.28.1, 1.29.2, 1.29.3) miały
sekcję „Nowe”, ale dodawały wyniki ewaluacji i dokumentację, a nie nowe API. Zgodnie z regułą 3 SemVer wydanych
wersji nie zmieniamy. Kontrola rodzaju podbicia obowiązuje od 1.35.0.
