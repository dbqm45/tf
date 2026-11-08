# Plan kroku 1: `.tf/`, format ustalenia i rdzeń `tf analyze` z piętrem 0

Stan: 2026-11-08, w realizacji. Plan nadrzędny: `docs/plans/2026-11-08-tf-analyze-i-katalog-tf.md` (sekcje 0–5,
„Kolejność realizacji”, krok 1). Zakres na teraz (decyzja człowieka 2026-11-08): `tf analyze` i porządek w katalogach;
format rejestru i ustalenia ma się dać później zmapować na kontrakt pdi (luki L1, L2, L6 w `docs/todo.md`), bez
integracji teraz.

## Zakres
- `tf init` — szkielet `.tf/` w projekcie (bez mapy repo i stacku — te przyjdą z modułami w kroku 2).
- `tf analyze [--only m1,m2] [--since <commit>] [--list] [--top N]` — rdzeń: wybór modułów, piętro 0 (skrypty),
  wspólny format ustalenia ze stabilnym `id`, deduplikacja, ranking, raport `.tf/reports/<moduł>.md` ze scalaniem
  checkboxów, pełna lista `.tf/reports/<moduł>.json`, przegląd `.tf/reports/README.md`, rejestr
  `.tf/register/items.jsonl`, cache po commicie.
- Poza zakresem kroku 1: piętra 1–3 i budżet (raport mówi jawnie, że ich nie było), moduły z nakładek i ich bramka
  (krok 2), migracja starych ścieżek (krok 4). Rdzeń nie ma jeszcze żadnego modułu — `tf analyze --list` mówi to
  wprost; testy używają modułu z katalogu tymczasowego.

## Pliki
| Plik | Co |
|---|---|
| `core/factory/analyze.py` | `init`, `run`, `list`; tylko biblioteka standardowa + `packs.load_yaml` (PyYAML z `_vendor`) |
| `core/factory/tf.py` | `tf init`, `tf analyze …` delegują do `factory/analyze.py` (jak `tf list` do `packs.py`) |
| `core/tests/test_analyze.py` | testy (najpierw czerwone) |
| `core/factory/PUBLIC_API.md` | nowe polecenia, układ `.tf/`, format `analyzer.yaml`, ustalenia i rejestru |
| `core/guide/FAQ.md` | krótko: co to `.tf/` i `tf analyze` |

## Kontrakty
**Układ `.tf/` po `tf init`:** `config.yaml`, `reports/README.md`, `register/README.md`, `cache/`, `logs/`, `runs/`,
`backup/` (każdy katalog z krótkim `README.md`: co tu jest, kto pisze, czy w gicie, czy można usunąć). Git:
instalacja zespołowa (`mode: shared` w manifeście) — `.gitignore` dostaje `.tf/cache/`, `.tf/logs/`, `.tf/runs/`,
`.tf/backup/`; instalacja prywatna (domyślna) — cały `.tf/` trafia do `.git/info/exclude`, jak reszta fabryki.
Polecenie jest idempotentne (nie nadpisuje istniejących plików) i wypisuje mapę `.tf/`.

**`config.yaml`:** `analyze: {top: 10, modules: {}}`, `project_record: docs/project`.

**Moduł** (`<katalog>/<nazwa>/analyzer.yaml`): `name`, `prefix` (np. `SEC`), `title`, `description`, `version`,
`applies_when` (opcjonalnie `files_any: [glob…]` — moduł stosowany, gdy w repo jest choć jeden pasujący plik),
`tier0: {script: scripts/<plik>.py}`. Katalogi modułów: `factory/analyzers/` i `.tf/analyzers/` (własne moduły
projektu); zmienna `TF_ANALYZERS_PATH` dokłada katalogi (testy, rozwój nakładek).

**Skrypt piętra 0:** `python3 <script> --root <repo> [--files a,b]` → na stdout JSON Lines, jedno ustalenie na linię:
`rule`, `title`, `file`, `line`, `snippet`, `severity` (`krytyczna|wysoka|średnia|niska`), `confidence` (0–1),
`evidence`, `basis`, `suggestion`. Kod ≠ 0 = moduł nie powiódł się (raport mówi to w zakresie; inne moduły dalej).

**Ustalenie po rdzeniu:** + `id` = `<prefix>-<6 hex sha1(rule|file|znormalizowany snippet)>` (bez numeru linii —
przesunięcie kodu nie zmienia id), `module`, `first_seen`, `commit`. Typy zgodne z kontraktem pdi dojdą przy
integracji (L6) — pole `kind` zostawione na `finding`.

**Rejestr `.tf/register/items.jsonl`:** jedna pozycja na linię, posortowane po `id`, przepisywane w całości (mały
diff w gicie): `id`, `kind: finding`, `module`, `title`, `status` (`otwarte|rozstrzygnięte`), `source: tf analyze`,
`refs` (`file:line`), `created`, `updated`, `note` (adnotacja rdzenia). Statusy z planu nadrzędnego (w toku,
zablokowane, czeka na człowieka) dojdą z pętlą pracy.

**Raport `.tf/reports/<moduł>.md`:** nagłówek, `Werdykt: OK | DO POPRAWY · data · commit · zakres · koszt: 0 USD
(piętro 0)`, `## Zakres` (co zbadano, piętra pominięte i dlaczego), `## Ustalenia` (top N po wadze × pewność),
`## Rekomendowane działania` (checkboxy `- [ ] <id> — <tytuł> (<plik>:<linia>) — <waga>` + wcięte notatki człowieka),
`## Historia analiz`. Scalanie przy ponownej analizie po `id`: odhaczone, a nadal widoczne → zostaje `[x]`
z adnotacją „analiza wciąż widzi problem”; nieodhaczone, a zniknęło → adnotacja „wygląda na naprawione — potwierdź”;
odhaczone i zniknęło → `[x]`, status rejestru `rozstrzygnięte`; nowe na końcu; notatki człowieka i kolejność ręczna
bez zmian. Odhaczenie w raporcie = status `rozstrzygnięte` w rejestrze.

**Cache:** `.tf/cache/analyze/<moduł>.json` z `commit`, `version` modułu i ustaleniami; ten sam commit, wersja
i czyste drzewo → wynik z cache bez uruchamiania skryptu. `--since <commit>`: skrypt dostaje tylko pliki zmienione od
`<commit>` (`--files`), ustalenia dla pozostałych plików z poprzedniego `<moduł>.json`.

## Testy (`core/tests/test_analyze.py`, kolejność = kolejność kodu)
1. A-1 `init`: struktura `.tf/`, README w katalogach, idempotencja (drugi raz nie nadpisuje zmienionego pliku).
2. A-2 `init` git: prywatna → `.tf/` w `.git/info/exclude`; zespołowa → wpisy w `.gitignore`.
3. A-3 `list`: brak modułów → komunikat wprost; z `TF_ANALYZERS_PATH` → nazwa, opis, czy stosuje się do repo.
4. A-4 `run`: raport, `.json`, rejestr; `id` stabilne przy przesunięciu linii; deduplikacja tych samych ustaleń.
5. A-5 ranking i `--top`: w raporcie top N, w `.json` wszystkie.
6. A-6 scalanie: `[x]` + notatka człowieka zostają; zniknięte nieodhaczone → „potwierdź”; odhaczone → rejestr
   `rozstrzygnięte`; odhaczone, a nadal widoczne → adnotacja.
7. A-7 cache i `--since`: drugi przebieg na tym samym commicie nie uruchamia skryptu; `--since` przekazuje tylko
   zmienione pliki i zachowuje ustalenia pozostałych.
8. A-8 odporność: skrypt z kodem ≠ 0 albo złym JSON → moduł oznaczony w zakresie raportu, pozostałe moduły działają,
   kod wyjścia 1; `applies_when` niespełnione → moduł pominięty z powodem.
9. A-9 `tf.py`: `tf init` i `tf analyze --list` docierają do `factory/analyze.py`.
10. A-10 raport przechodzi `claims_check.py` (gdy skrypt jest w projekcie).

## Weryfikacja przed PR
`python3 tools/workspace.py check --packs none` (i `all`), testy `tests/`, `python3 tools/workspace.py refs`.
Hooki fabryki w tej sesji nie działają (sesja z wieloma repozytoriami w chmurze) — testy i bramki uruchamiane ręcznie.
