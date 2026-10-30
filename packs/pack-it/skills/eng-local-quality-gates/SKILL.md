---
name: eng-local-quality-gates
description: Użyj przy lokalnych bramkach jakości — hook po edycji, pre-commit, pre-push, testy powiązane.
metadata:
  przeglad: "2027-10-09"
  katalog: "Użyj przy ustawianiu lokalnych bramek jakości w projekcie — rozmieszczenie lintu, formatowania, typów i testów między hookiem agenta po edycji, pre-commit, pre-push i CI; testy powiązane z edytowanym plikiem; kody wyjścia i informacja zwrotna dla agenta; zachowanie agenta przy padającym hooku; Husky, lint-staged, Lefthook, pre-commit; szablon hooka post_edit_checks.py z konfiguracją quality-gates.json. Nie do pipeline'ów CI (ops-ci-cd), gałęzi, commitów i PR (core-git-workflow), uprawnień agenta (core-agent-security) ani doboru zestawów regresji (qa-regression)."
  slowa: "hook po edycji, hook PostToolUse, pre-commit, pre-push, husky, lint-staged, lefthook, formatowanie po edycji, lint przy zapisie, testy powiązane z plikiem, vitest related, findRelatedTests, bramka przed commitem, git hooks, hooki gita, agent dostaje błąd lintera, szybka informacja zwrotna"
---

# Lokalne bramki jakości

Cel: błąd formatu, lintu, typu albo zepsuty test w obszarze ryzyka wychodzi na maszynie, w sekundach od edycji, a nie
po 20 minutach w CI. Hook agenta jest warstwą deterministyczną: działa niezależnie od tego, co model pamięta z instrukcji,
także po kompaktowaniu kontekstu. CI nadal uruchamia pełny zestaw — warstwy lokalne go nie zastępują.

## Gdzie które sprawdzenie
| Warstwa | Co | Budżet czasu | Uwagi |
|---|---|---|---|
| po edycji (hook agenta) | format i lint jednego pliku; testy powiązane z plikiem z obszaru ryzyka | sekundy | jedyna warstwa, która mówi agentowi o błędzie w trakcie pracy |
| pre-commit (git) | lint i format plików w stage; typy; ewentualnie testy powiązane z plikami w stage | kilkanaście s | łapie też edycje ręczne i spoza agenta |
| pre-push (git) | pełne typy, szerszy zestaw testów | minuty | |
| CI | integracja, pełne E2E, skany, build | minuty i więcej | ops-ci-cd |

- Sprawdzenie dłuższe niż kilka sekund → o warstwę wyżej albo zawęź do pliku.
- Hook po edycji działa osobno dla każdej edycji (3 pliki = 3 uruchomienia), bez agregacji.
- Zacznij od jednego hooka (format/lint) i jednej bramki commitowej; dokładaj, gdy widzisz, co ucieka.
- Bramki wynikają ze strategii testów projektu (qa-test-design, sekcja „Bramki jakości”) — każda ma warstwę i fazę,
  od której obowiązuje.

## Procedura
1. **Inwentarz (tylko odczyt).** Polecenia lintu, formatu, typów i testów (`package.json`, `pyproject.toml`), istniejące
   hooki (`.husky/`, `lefthook.yml`, `.pre-commit-config.yaml`, sekcja `hooks` w `.claude/settings.json`), strategia
   testów (`docs/project/05-plan/test-strategy.md`). Działającej konfiguracji nie migrujesz na inne narzędzie.
2. **Rozmieść sprawdzenia** wg tabeli wyżej; dla testów powiązanych wypisz globy obszarów ryzyka (np. `src/billing/**`),
   nie cały `src/`.
3. **Hook agenta po edycji** — szablon niżej. Zmiana `.claude/settings.json` i `.claude/hooks/` tylko na prośbę
   człowieka (CLAUDE.md); bez zgody oddajesz gotowy fragment do wklejenia.
4. **Hooki gita** — `references/hooki-gita.md` (Husky + lint-staged, Lefthook, pre-commit; wersje sprawdzone).
5. **Test bramek:** edycja pliku → hook się uruchamia → błąd wraca do agenta; zepsuty plik w stage → commit odrzucony;
   czerwony test → push odrzucony. Bez tego bramka jest życzeniem.
6. **Zapis:** tabela „bramka → warstwa → od kiedy” w strategii testów; polecenia w sekcji „Komendy” w `CLAUDE.md` projektu.

## Model hooka agenta
zdarzenie (po użyciu narzędzia) → filtr (narzędzie `Edit|Write`, wzorzec ścieżki) → akcja (polecenie) → sygnał
(kod wyjścia i wyjście, które wraca do agenta). Ścieżka pliku jest w JSON na stdin: `tool_input.file_path`.

| Kod wyjścia hooka (Claude Code) | Skutek |
|---|---|
| 0 | OK; JSON na stdout może dodać `hookSpecificOutput.additionalContext` (kontekst dla modelu) lub `systemMessage` (dla człowieka) |
| 2 | błąd blokujący — treść stderr trafia do modelu jako komunikat hooka |
| inny | błąd nieblokujący — widoczny w trybie szczegółowym, model go nie dostaje |

Hook, którego wynik nie wraca do agenta, nie nauczy go poprawki. Konfiguracja: `.claude/settings.json` (projekt, w repo),
`.claude/settings.local.json` (lokalna, poza repo), `~/.claude/settings.json` (użytkownik).

### Szablon: `templates/post_edit_checks.py` + `.claude/quality-gates.json`
Gotowy hook (biblioteka standardowa Pythona, test: `tests/test_post_edit_checks.py`). Bramki opisujesz w JSON,
bez pisania hooka od zera; przykład: `templates/quality-gates.example.json`.
- brak konfiguracji albo pasującego `glob` → nic; porażka polecenia → kod 2 i ostatnie `max_lines` linii na stderr;
- polecenie bez powłoki, `{file}` = ścieżka względna edytowanego pliku (jeden argument, także ze spacjami);
- przekroczony `timeout`, brak programu, zła konfiguracja → kod 0 i komunikat „zawęź albo przenieś do pre-commit”;
- własny limit całego hooka `CLAUDE_QG_DEADLINE` (domyślnie 50 s, kończy się kodem 0 przed limitem Claude Code);
  UTF-8 wymuszone na stdin/stdout/stderr (Windows); `CLAUDE_QUALITY_GATES=off` wyłącza hook;
- `python3 .claude/hooks/post_edit_checks.py --dry-run src/billing/invoice.ts [--json]` pokazuje, które sprawdzenia
  obejmą plik — niczego nie uruchamia.

Instalacja w projekcie (za zgodą człowieka): skopiuj szablon do `.claude/hooks/`, konfigurację do
`.claude/quality-gates.json`, a w `.claude/settings.json`:
```json
"PostToolUse": [
  { "matcher": "Edit|Write",
    "hooks": [ { "type": "command", "command": "python3",
                 "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/post_edit_checks.py"], "timeout": 60 } ] }
]
```

## Testy powiązane z plikiem
| Runner | Polecenie | Uwagi (sprawdzone 2026-10-10) |
|---|---|---|
| Vitest 5 | `vitest related <plik> --run` | `related` to podkomenda; `--run` wyłącza tryb watch; brak powiązanych testów → kod 0 |
| Jest 30 | `jest --findRelatedTests <plik>` | flaga, nie podkomenda |
| pytest | `pytest --testmon` (wtyczka pytest-testmon) albo mapa plik → katalog testów | brak natywnego odpowiednika |

- Vitest 5 w środowisku agenta (wykrywa m.in. `AI_AGENT`, którą ustawia Claude Code) domyślnie wybiera reporter
  `minimal` (alias `agent`) i wyłącza watch — mniej szumu w kontekście.
- Testy powiązane tylko dla globów ryzyka, nie dla helperów i konfiguracji.
- Wyjście ogranicz do końcówki (szablon: `max_lines`).

## Agent a padający hook
- **Trywialne** (format, import, typ, nieużywana zmienna) — agent poprawia sam w następnym kroku.
- **Test logiki** pada po 1–2 próbach poprawki → stop: przyczyna wg eng-debugging albo pytanie do człowieka. Nie
  dopasowujesz kodu na ślepo do zielonego i nie osłabiasz testu (tdd_guard, qa-spec-first-testing).
- Bramki gita nie obchodzisz (`--no-verify`, `HUSKY=0`, `LEFTHOOK=0`); padła → poprawka przyczyny, nowy commit.
- Hook, który regularnie przekracza limit, przenosisz wyżej — nie wydłużasz `timeout` w nieskończoność.

## Inne narzędzia agentowe
Cursor, Codex, Windsurf i Copilot mają ten sam model (zdarzenie → filtr → polecenie), ale inne pliki, nazwy zdarzeń
i pola wejścia; część narzędzi tylko blokuje i nie przekazuje wyniku agentowi. Hook przeniesiony 1:1 sprawdź z bieżącą
dokumentacją danego narzędzia (core-source-research) i testem z kroku 5. [niezweryfikowane: szczegóły per narzędzie]

## Przykład
**Sytuacja:** projekt TS (Vitest 5, ESLint), ryzyko #1 ze strategii testów — rozliczenia w `src/billing/`. CI trwa
18 minut, a agent co drugi PR oddaje kod z błędem lintu.
**Wynik:**

| Bramka | Warstwa | Od kiedy |
|---|---|---|
| `npx eslint --fix {file}` dla `src/**/*.{ts,tsx}` | po edycji (`post_edit_checks.py`) | od razu |
| `npx vitest related {file} --run` dla `src/billing/**/*.ts` | po edycji | po fazie 1 strategii (testy rozliczeń istnieją) |
| lint-staged (`eslint --fix`, `prettier --write`) + `npx tsc --noEmit` | pre-commit (Husky) | od razu |
| `npx vitest run` | pre-push | od razu |
| pełne E2E, build, skany | CI | bez zmian |

Test bramek: nieużywany import w `src/billing/invoice.ts` → hook zwrócił kod 2 z błędem ESLint, agent poprawił w następnym
kroku; ten sam błąd wprowadzony ręcznie → commit odrzucony przez lint-staged.

## Checklista
- [ ] każda bramka ze strategii testów ma warstwę i fazę, od której obowiązuje
- [ ] hook po edycji trwa sekundy; testy powiązane tylko dla globów ryzyka
- [ ] porażka wraca do agenta (kod 2 / stderr), błąd samego hooka nie blokuje pracy
- [ ] zmiana `settings.json`/`.claude/hooks/` tylko za zgodą człowieka
- [ ] bramki przetestowane (edycja, commit, push); wynik w raporcie
- [ ] CI nadal uruchamia pełny zestaw

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 3, lekcja o hookach i lokalnych warstwach jakości — materiał szkoleniowy (dostęp 2026-10-09).
- Claude Code — dokumentacja hooków (code.claude.com/docs/en/hooks): zdarzenie PostToolUse, kody wyjścia, `additionalContext`;
  obsługa kodu 2 i komunikatu stderr potwierdzona w kodzie Claude Code 2.1 (2026-10-10).
- Vitest 5.0.3 `--help` i kod źródłowy (`related`, reporter `agent`/`minimal`, wykrywanie agenta przez std-env), Jest 30.5.2
  `--help`, pytest-testmon 2.2.0 `--help` — sprawdzone lokalnie 2026-10-10.
- Husky 9.1.7, lint-staged 17.6.0, Lefthook 2.2.1, pre-commit 4.6.2 — rejestry npm/PyPI i walidacja konfiguracji 2026-10-10.
