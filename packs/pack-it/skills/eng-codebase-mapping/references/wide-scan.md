# Szeroki skan repo — narzędzia, legenda, sprzężenia

## 1. Wyszukiwanie: która rodzina na jakie pytanie
| Pytanie | Rodzina | Narzędzie | Pułapka |
|---|---|---|---|
| gdzie pada słowo lub wzorzec | tekstowa | `rg` | wymaga słownika projektu; łapie komentarze i stringi |
| gdzie definicja, sygnatura, wywołanie symbolu | strukturalna / symboliczna | ast-grep, ctags, LSP („find references”), SCIP | zły wzorzec = puste trafienie bez błędu → zero potwierdzasz `rg` |
| kto importuje moduł | graf zależności | madge, dependency-cruiser, jdeps, `nx graph` | nie widzi zależności runtime |
| „coś jak…”, nie znam nazwy | semantyczna (embeddingi) | indeks RAG | nieświeży indeks, wynik probabilistyczny |
| jak przepływ idzie przez warstwy | agentowa (iteracyjna) | subagent | w szerokim skanie trzymaj krótko — to zadanie pogłębienia |
Narzędzie reklamowane jako „semantic search” bywa strukturalne (AST), a nie wektorowe — nie przypisuj mu
przybliżonej pewności, dopóki nie sprawdzisz, jak działa.

Binarka ast-grepa to `ast-grep` (pakiety: npm `@ast-grep/cli`, pip `ast-grep-cli`, cargo `ast-grep`). Paczka
instaluje też alias `sg`, ale na Linuksie `/usr/bin/sg` (pakiet `login`) uruchamia polecenie z inną grupą —
w skryptach i instrukcjach używaj pełnej nazwy.

## 2. dependency-cruiser, gdy graf jest kłębkiem (sprawdzone na 18.5.0)
| Dźwignia | Flaga | Kiedy |
|---|---|---|
| węzły = foldery | `--collapse "^src/[^/]+"` albo `--collapse 2` | pierwszy widok dużego repo |
| w dół od modułu | `--focus "^src/billing" --focus-depth 1` | sąsiedzi jednego modułu |
| kto prowadzi do X | `--reaches "^src/db/"` | zasięg zmiany w module bazowym |
| metryki stabilności | `--metrics` (Ca, Ce, niestabilność) | kandydaci na moduły nośne |
| widok architektury | `-T archi` (albo `-T mermaid`, `-T dot`) | diagram do mapy |
| zmienione od rewizji | `--affected <rewizja>` | wpływ diffu |
**Pułapka:** `--do-not-follow node_modules` (lub `doNotFollow` w konfiguracji) zostawia paczki jako liście grafu.
Żeby zniknęły z obrazu, wyklucz je: `--exclude "node_modules|\.test\.|\.spec\.|\.stories\.|__snapshots__|\.d\.ts$"`.
Najpierw wynik tekstowy z tabelą (obszar · ustalenie · dowód · dlaczego ważne · co dalej); render SVG tylko dla
jednego podgrafu, który odpowiada na jedno pytanie. Wymaga zainstalowanego toolchainu projektu (TS: `tsconfig`).

## 3. Graf poza JS/TS i ślepe plamy
| Ekosystem | Narzędzie (sprawdź składnię w dokumentacji wersji) | Ślepa plama |
|---|---|---|
| Java | `jdeps`, ArchUnit, `mvn dependency:tree`, graf modułów Gradle | refleksja, `Class.forName`, DI z konfiguracji |
| Python | Tach, pydeps, import-linter | importy dynamiczne (`importlib`), wtyczki przez entry points |
| Go | `go mod graph`, goda | interfejsy spełniane niejawnie |
| .NET | graf referencji projektów (`dotnet list reference`) | DI w `Program.cs`, refleksja |
| Swift | `swift package show-dependencies` | — |
| TS | madge, dependency-cruiser, skott | aliasy ścieżek bez `tsconfig` gubią importy |
Ślepe plamy wpisujesz do sekcji „Ograniczenia” mapy.

## 4. Terytorium z historii — jak czytać wynik `git_territory.py`
- **Ranking katalogów i plików:** gdzie toczy się praca. Gdy na szczycie stoi zbyt ogólny katalog, zwiększ `--depth`.
- **Kwartały:** katalog na szczycie w każdym kwartale = stałe centrum (rdzeń); jeden kwartał = kampania (migracja,
  przepisanie) — sprawdź, czy skończona.
- **Pary współzmian:** udział ≥ 0,8 (prawie zawsze razem) = ukryta umowa między plikami — kandydat na connascence
  znaczenia lub algorytmu (ddd-connascence-analysis). Para wynikająca z regeneracji (kod generowany + schemat) jest
  tańsza niż ręczna edycja — oznacz to.
- **Huby:** plik zmieniany z wieloma obszarami (konfiguracja, tłumaczenia, rejestr tras) = szeroki zasięg zmiany;
  ranking hubów ≠ ranking par.
- **Współzmiany kłamią w obie strony:** masowe commity sklejają niezwiązane pliki (dlatego `--max-files`); brak
  współzmian nie dowodzi braku umowy (model backendu i jego ręczna kopia na froncie, które NIE zmieniają się razem,
  to cichy dług → `unknown` do sprawdzenia w kodzie).
- **Usunięte pliki** z rankingu: przeszłość. Nie wpisuj ich do trasy czytania.

## 5. Legenda modułów
| Oś | Wartości | Dowód |
|---|---|---|
| rola | core / supporting / peripheral | punkt wejścia, publiczny kontrakt, główny przepływ produktu — nie nazwa folderu |
| głębokość | deep / shallow | wewnętrzne rozgałęzienia i reguły vs router, adapter, wrapper (eng-module-depth) |
| profil zmian | stable / volatile / seasonal | ranking kwartalny |
| zasięg | load-bearing / contained | wysokie Ca, kontrakty, auth, dane, cache, migracje, konfiguracja runtime |
| wrażliwość | high / medium / low | suma powyższych + cykle + integracje |
Wpis modułu: rola · evidence (lista) · inference · caution (co sprawdzić przed zmianą) · unknowns. Etykieta bez
dowodu to domysł → `do weryfikacji`.

## 6. Rodzaje sprzężenia na mapie
| Rodzaj | Skąd wiesz | Uwagi |
|---|---|---|
| przychodzące / wychodzące | graf importów | Ca / Ce |
| kontraktowe | wspólne typy, DTO, schematy | zmiana kontraktu = zmiana wszystkich stron |
| runtime | DI, flagi, kolejki, webhooki, refleksja, dynamiczny import, codegen | graf ich nie widzi → zawsze w `unknowns`, chyba że sprawdzone w kodzie |
| współzmianowe | historia gita | para vs hub; regeneracja tańsza niż ręczna edycja |
Przy każdym sprzężeniu podaj źródło: graf importów / historia / „narzędzie nie objęło”.
