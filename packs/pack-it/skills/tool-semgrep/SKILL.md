---
name: tool-semgrep
description: Użyj przy pisaniu własnych reguł Semgrep (i zapytań CodeQL) — wzorce, taint, autofix, testy reguł, mniej fałszywych trafień, CI.
metadata:
  przeglad: 2027-01-24
  katalog: "Użyj, gdy piszesz, testujesz lub poprawiasz własną regułę Semgrep albo zapytanie CodeQL — składnia reguły (pattern, patterns, pattern-either, pattern-inside, pattern-not, metazmienne, metavariable-regex, focus-metavariable), tryb taint (źródła, sanityzatory, ujścia), autofix (fix:) z testem poprawki (.fixed), testy reguł (ruleid:, ok:, todoruleid:, todook:, semgrep scan --test), ograniczanie fałszywych trafień (ograniczenia metazmiennych, paths.exclude, przypadki ok: z prawdziwych alarmów), reguły w CI (testy reguł, --baseline-commit, --error), licencje reguł z rejestru, testy zapytań CodeQL (.qlref, .expected, codeql test run). Nie do szukania wariantów znalezionej podatności (sec-variant-analysis), doboru skanerów i progów w programie AppSec (sec-appsec-devsecops) ani reguł detekcji w SIEM (sec-detection-engineering)."
  slowa: "semgrep, własna reguła semgrep, napisać regułę semgrep, reguła semgrep fałszywe trafienia, false positives semgrep, mode: taint, pattern-sources, pattern-sinks, pattern-sanitizers, pattern-not, pattern-inside, metavariable-regex, focus-metavariable, ruleid, todoruleid, semgrep --test, test reguły, autofix semgrep, fix:, .fixed, baseline-commit, .semgrepignore, opengrep, codeql test run, qlref, zapytanie codeql test"
---

# Semgrep — własne reguły z testami

Kiedy pisać regułę po znalezionej podatności: sec-variant-analysis. Program skanerów i progi: sec-appsec-devsecops.
Ten skill to rzemiosło reguły: składnia, testy, precyzja, CI.

## Procedura
1. **Najpierw test, potem reguła.** Plik testu o tej samej nazwie bazowej co reguła (reguła x.yaml, test x.py):
   kod podatny z `# ruleid: <id>` nad linią trafienia, poprawny z `# ok: <id>`. Najlepsze przykłady to prawdziwy
   kod sprzed naprawy i prawdziwe fałszywe alarmy. Znana luka reguły → `todoruleid:`, znany fałszywy alarm →
   `todook:` (test przechodzi, dług jest widoczny).
2. **Najwęższa składnia, która wystarcza**:
   - jedno wywołanie → `pattern`; kilka form → `pattern-either`; warunki łączne → `patterns`;
   - kontekst → `pattern-inside` / `pattern-not-inside`; wyjątki → `pattern-not`;
   - warunek na treści → `metavariable-regex` / `metavariable-pattern`; miejsce zgłoszenia → `focus-metavariable`;
   - dane płyną przez zmienne i funkcje → `mode: taint` ze źródłami, ujściami i **sanityzatorami** (bez nich
     każda poprawna ścieżka to alarm).
   Pełne nazwy modułów (`flask.request`, `subprocess.run`) — Semgrep rozwiązuje importy i aliasy.
3. **Komunikat mówi, jak naprawić**, nie tylko co jest źle; `metadata` z CWE i `confidence`. `severity: ERROR`
   tylko dla reguł, które mają blokować merge.
4. **Autofix** (`fix:` z metazmiennymi) tylko dla zamiany jednoznacznej; test poprawki w pliku x.fixed.py.
   Na kodzie najpierw `--autofix --dryrun`, zmiany przez przegląd jak każdy commit.
5. **Precyzja przed wdrożeniem**: uruchom regułę na całym repozytorium, przejrzyj próbkę trafień i policz
   odsetek prawdziwych. Każdy fałszywy alarm → przypadek `ok:` w teście → zawężenie reguły (ograniczenia
   metazmiennych, `pattern-not`, kontekst). Kod testowy i przykłady → `paths.exclude` w regule albo
   `.semgrepignore`. Reguła blokująca z wieloma fałszywymi alarmami zostanie wyłączona — wtedy `WARNING` albo
   tylko raport, dopóki precyzja nie wzrośnie.
6. **CI**: reguły w repozytorium (np. `.semgrep/`); najpierw `semgrep scan --test` dla reguł, potem skan PR
   z `--baseline-commit` (tylko nowe trafienia) i `--error` (kod 1 przy trafieniu); całe repozytorium nocą.
   `--metrics=off`, gdy polityka zabrania telemetrii.
7. **Licencje**: silnik Semgrep CE i fork Opengrep — LGPL-2.1; reguły z rejestru (`semgrep/semgrep-rules`) mają
   osobną licencję „Semgrep Rules License v1.0” — przed użyciem w produkcie lub usłudze przeczytaj jej warunki
   [niezweryfikowane: treść warunków, semgrep.dev niedostępne z sesji]. Własne reguły są Twoje.

## CodeQL — testy zapytań
Gdy wariant wymaga pełnej analizy przepływu między plikami, regułą jest zapytanie CodeQL (sec-variant-analysis,
krok 3). Testy wg dokumentacji GitHub: osobna paczka testowa z plikiem qlpack.yml (`extractor: <język>`, zależność od
paczki z zapytaniami, `codeql pack install`), w katalogu testu kod przykładowy, plik `.qlref` ze ścieżką zapytania
i `.expected` o tej samej nazwie bazowej. `codeql test run <katalog>` buduje bazę z przykładów, zapisuje `.actual`
i pokazuje różnicę z `.expected`; świadomie zaakceptowany wynik — `codeql test accept`. Nie sprawdzone lokalnie
(pobranie CLI zablokowane w sesji).

## Przykład
Reguła `shell-injection-from-request` (taint: `request.args.get` → pierwszy argument `subprocess.run(...,
shell=True)`, sanityzator `shlex.quote`) z testem: dwa `ruleid`, dwa `ok`, jeden `todoruleid` (wartość przez
obiekt pomocniczy). `semgrep scan --test` przechodzi; po usunięciu sanityzatora test oblewa na linii z
`shlex.quote` — dowód, że test pilnuje reguły. Kod tej reguły, autofixu `yaml.load` → `yaml.safe_load` z plikiem
.fixed.py i reguły na hasła z `paths.exclude`: `references/reguly-i-testy.md`.

## Zależne od wersji
Przykłady z `references/reguly-i-testy.md` przechodzą na 1.50.0, 1.100.0 i 1.182.1 (2026-10-24); progi podpoleceń
sprawdzone `semgrep --help` kolejnych wydań z PyPI (1.99.0 bez `test`, 1.149.0 bez `mcp`). Wydania co tydzień.
| Wersja | Zmiany istotne dla tego skilla |
|---|---|
| 1.50 | `scan --test` z `ruleid`/`ok`/`todoruleid`/`todook` i testami poprawek `.fixed`, tryb taint, `--baseline-commit` |
| 1.100 | podpolecenie `semgrep test` (eksperymentalne, obok `semgrep validate`); `scan --test` dalej działa |
| 1.150 | podpolecenie `semgrep mcp` (serwer MCP Semgrepa — ocena przed podłączeniem: core-agent-security) |
Projekt z wersją starszą niż 1.50 → `PROJECT_OLDER`: sprawdź przykłady testem przed użyciem.

## Checklista
- [ ] test reguły z `ruleid` i `ok` (w tym prawdziwe fałszywe alarmy), test oblewa po zepsuciu reguły
- [ ] taint ma sanityzatory; `focus-metavariable` wskazuje właściwe miejsce
- [ ] komunikat z naprawą, CWE w `metadata`, `severity` zgodne z tym, czy reguła blokuje
- [ ] precyzja zmierzona na repozytorium przed włączeniem blokowania
- [ ] CI: testy reguł, potem skan PR z `--baseline-commit` i `--error`

## Źródła
- Semgrep 1.50.0, 1.100.0, 1.182.1 (PyPI) — przykłady, `--baseline-commit`, `--validate`, `todook` sprawdzone
  w działaniu 2026-10-24; `semgrep scan --help`.
- Licencje: `LICENSE` w `semgrep/semgrep`, `semgrep/semgrep-rules`, `opengrep/opengrep` (GitHub, odczyt 2026-10-24).
- GitHub Docs, „Testing custom queries”, „Query reference files”, `codeql test accept` (github/docs, commit
  02c25d1, 2026-10-23).
- Inspiracja tematu: Trail of Bits `semgrep-rule-creator` — treści nie przejęto.
Opisane własnymi słowami.
