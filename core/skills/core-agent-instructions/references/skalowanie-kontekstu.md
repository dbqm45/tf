# Skalowanie kontekstu agenta w dużym projekcie

> **Spis treści:** 1. Trzy rodzaje kontekstu — trzy miejsca · 2. Cztery awarie przerośniętego pliku · 3. Drabina dojrzałości i sygnały przejścia wyżej · 4. Jak Claude Code ładuje pliki instrukcji (stan sprawdzony) · 5. CLAUDE.md w module — wzorzec i indeks w root · 6. Plik modułu czy reguła z `paths` · 7. Utrzymanie i przegląd reguł · 8. Wiele repozytoriów · 9. Wynik i przykład

Pytanie nie brzmi „co agent ma wiedzieć”, tylko „co ma wiedzieć **teraz**”. Stały kontekst zabiera uwagę zadaniu.

## 1. Trzy rodzaje kontekstu — trzy miejsca
| Rodzaj | Co to jest | Gdzie |
|---|---|---|
| konwencje | jak pracujemy, czego nie widać z kodu | `CLAUDE.md` (root + moduły), `.claude/rules/` |
| referencje | PRD, plany, research, decyzje, mapy kodu | `docs/project/` (core-project-record) — czytane, gdy potrzebne |
| procedury | powtarzalne kroki z punktami decyzji | skille, komendy |

Główny `CLAUDE.md` to spis treści, nie encyklopedia: polecenia, konwencje globalne, wskaźniki do reszty.

## 2. Cztery awarie przerośniętego pliku
1. **Wypiera zadanie** — zajmuje kontekst, który powinien należeć do bieżącej pracy.
2. **Rozcieńcza** — gdy wszystko jest ważne, nic nie jest; reguły ze środka giną.
3. **Gnije** — reguły starzeją się szybciej, niż ktoś je przegląda; nieaktualna reguła szkodzi bardziej niż brak.
4. **Nie da się sprawdzić**, czy agent go przestrzega — za dużo reguł na jedno zadanie.

Kolejność naprawy: najpierw higiena (wytnij wg testu włączenia w SKILL.md), dopiero potem struktura (podział).

## 3. Drabina dojrzałości i sygnały przejścia wyżej
Wchodzisz wyżej na żądanie, nie po kolei i nie „na zapas”.
1. **Root `CLAUDE.md` + `docs/project/`** — domyślnie; dla MVP i małych repo tak długo, jak się da.
2. **`CLAUDE.md` w module + indeks w root** — moduł ma własne, szczegółowe konwencje nieistotne dla reszty albo
   osobnego właściciela.
3. **Własny katalog dokumentacji w module** (plany, decyzje modułu) — gdy prowadzi go osobny zespół albo praca
   w module jest intensywna i długa.

Sygnały do wejścia wyżej (co najmniej jeden, z dowodem zapisanym w wyniku):
- root powyżej ~200 niepustych linii mimo higieny (skrypt `instructions_lint.py`);
- agent powtarza błąd w module mimo reguły w root (wpisz konkretne przypadki: data, plik, co zrobił);
- przy każdej pracy w module podajesz te same referencje ręcznie;
- moduł ma własny deploy, własnego właściciela w CODEOWNERS albo inny stack.

Liczba katalogów i poczucie „to duża aplikacja” **nie** są sygnałem. Dziel według granic własności, nie wielkości.
Nie zakładaj `CLAUDE.md` młodego modułu, który jeszcze się zmienia — plik wolno zmieniający się nie trzyma faktów
szybko zmieniających się (nazwy plików w ruchu, liczby, wersje).

## 4. Jak Claude Code ładuje pliki instrukcji (stan sprawdzony)
Źródło: code.claude.com/docs/en/memory i …/large-codebases, dostęp 2026-10-10. Zachowanie zależy od wersji —
przy wątpliwości sprawdź `/context` (lista „Memory files”) w bieżącej sesji.
- **Przy starcie**: `CLAUDE.md` i `CLAUDE.local.md` z katalogu roboczego i wszystkich katalogów nad nim, a także
  `~/.claude/CLAUDE.md` i plik zarządzany przez organizację. Pliki się **sklejają**, nie nadpisują; bliższy katalogowi
  roboczemu jest czytany później. Projektowy plik może leżeć w `./CLAUDE.md` albo `./.claude/CLAUDE.md`.
- **Na żądanie**: `CLAUDE.md` z podkatalogów ładuje się dopiero, gdy agent czyta pliki w tym podkatalogu. Start
  sesji z roota = plik modułu może jeszcze nie być w kontekście, gdy agent planuje. Reguła krytyczna modułu →
  start sesji w module albo jawne wskazanie pliku w poleceniu lub briefie subagenta.
- **Importy `@ścieżka`**: rozwijane przy starcie razem z plikiem, który je zawiera; ścieżki względne liczone od
  pliku z importem; do 4 poziomów zagnieżdżenia. Porządkują, ale **nie zmniejszają** kosztu kontekstu. Import
  w odwrotnych apostrofach (`` `@README` ``) i w bloku kodu nie jest wykonywany. Import spoza katalogu roboczego
  wymaga jednorazowej zgody człowieka.
- **`.claude/rules/*.md`**: bez pola `paths` ładują się przy starcie jak `.claude/CLAUDE.md`; z polem `paths`
  (lista globów) — dopiero gdy agent czyta lub edytuje pasujący plik. `paths` to jedyne pole, które Claude Code
  czyta z nagłówka reguły; błędny YAML = reguła ładowana zawsze.
- **AGENTS.md**: nowsze wersje Claude Code czytają `AGENTS.md` same, ale domyślnie **tylko wtedy, gdy w katalogu
  roboczym i wyżej nie ma `CLAUDE.md`, `.claude/CLAUDE.md` ani `CLAUDE.local.md`**. Gdy są oba pliki, Claude czyta
  tylko `CLAUDE.md` — dlatego wzorzec „AGENTS.md źródłem prawdy, CLAUDE.md z `@AGENTS.md`” działa niezależnie od
  wersji i ustawień. Uwaga: dodanie własnego `CLAUDE.local.md` w repo opartym na AGENTS.md wyłącza czytanie
  AGENTS.md (zmiana w ustawieniu „Project instructions” w `/config`). Dowiązanie `CLAUDE.md → AGENTS.md` działa,
  ale na Windows git może je wypakować jako zwykły plik tekstowy — tam bezpieczniejszy import.
- **Inne narzędzia** (Codex, Copilot): czytają `AGENTS.md` z drzewa katalogów; szczegóły pierwszeństwa sprawdź
  w ich dokumentacji dla używanej wersji [niezweryfikowane w tej sesji].
- **Rozmiar**: plik powyżej zalecanej długości daje ostrzeżenie przy starcie; Claude Code pomija plik większy niż
  4 MiB. Automatyczna pamięć (`~/.claude/projects/<projekt>/memory/MEMORY.md`) ładuje tylko pierwsze 200 linii lub
  25 KB — to notatki maszyny, nie miejsce na reguły zespołu.
- **Po `/compact`**: root `CLAUDE.md` jest wczytywany ponownie z dysku; pliki modułów i reguły z `paths` wracają
  dopiero, gdy agent znów dotknie pasującego pliku. Instrukcja podana tylko w rozmowie znika.
- **Monorepo z cudzymi pakietami**: `claudeMdExcludes` w `.claude/settings.local.json` (globy po ścieżkach
  bezwzględnych) pomija pliki instrukcji katalogów, w których nie pracujesz.

## 5. CLAUDE.md w module — wzorzec i indeks w root
- Pierwsza linia: „Tylko kontekst `<moduł>`. Zasady całego repo: główny CLAUDE.md.”
- Tylko to, czego nie da się wywnioskować z roota ani z kodu modułu: pułapki (prawdziwy punkt wejścia, zakazane
  API, wymagany logger), antywzorce, polecenia modułu (test, migracje). Zero kopii reguł roota.
- 10–40 linii; dłuższy plik modułu to sygnał, że część treści to referencja (do `docs/`) albo procedura (do skilla).
- Root kończy się sekcją **„Moduły z własnym CLAUDE.md”**: `ścieżka — jedno zdanie zakresu`. Skrypt
  `instructions_lint.py --root .` zgłasza plik modułu spoza tego indeksu i linie skopiowane z roota.
- Właścicielem pliku modułu jest właściciel modułu; zmiany przechodzą przegląd w PR jak dokumentacja.

## 6. Plik modułu czy reguła z `paths`
| Podejście | Gdzie leży | Ładuje się | Kiedy |
|---|---|---|---|
| `CLAUDE.md` w katalogu | obok kodu | przy starcie z tego katalogu albo gdy agent czyta tam plik | właściciel katalogu utrzymuje własne konwencje |
| reguła `.claude/rules/x.md` z `paths` | centralnie w root | gdy agent czyta/edytuje pasujący plik | wszystkie konwencje w jednym miejscu albo ta sama reguła dla rozproszonych plików (np. `**/*.test.ts`) |
| skill w `<moduł>/.claude/skills/` | w module | gdy zadanie pasuje do opisu | procedura modułu (testy, migracje), nie stała konwencja |

## 7. Utrzymanie i przegląd reguł
Przegląd co miesiąc lub kwartał (i po większym wydaniu modelu), dla każdej reguły pięć pytań:
1. Czy agent złamałby ją bez niej? (kalibracja A/B w SKILL.md, sekcja 6)
2. Czy wynika z kodu, lintera, typów albo hooka? → usuń.
3. Czy jest sprawdzalna w diffie?
4. Czy jest aktualna (ścieżki, polecenia, wersje istnieją)?
5. Czy dubluje albo przeczy innej regule w innym pliku?
Wpis w wyniku: data przeglądu, usunięte i dodane reguły z powodem. Hook `Stop`, który po sesji proponuje poprawki
CLAUDE.md, to opcja dla dojrzałych zespołów — propozycja trafia do człowieka, nie wprost do pliku.

## 8. Wiele repozytoriów
Trzy warstwy, od najprostszej:
1. **Wspólne reguły i skille w jednym repo-źródle**, wersjonowane (SemVer, core-semver).
2. **Dystrybucja z aktualizacją**: paczka → CLI → wtyczka lub serwer MCP (rosnąca złożoność). Każde repo i tak ma
   własny krótki `CLAUDE.md` z lokalnymi umowami. Szczegóły instalatora: `.claude/skills/core-skill-authoring/references/dystrybucja-w-zespole.md`.
3. **Widoczność innych repo w czasie pracy**: generowane kontrakty (OpenAPI, AsyncAPI, protobuf, GraphQL SDL),
   paczki testów kontraktowych, dokumentacja generowana w CI — zamiast meta-repo opisującego wszystko ręcznie
   (starzeje się najszybciej). Migawka całego repo do jednego pliku tylko doraźnie, do jednego zadania.

## 9. Wynik i przykład
Wynik decyzji o strukturze: `docs/project/04-architecture/context-architecture.md` — szczebel drabiny, sygnały
z dowodami, indeks plików instrukcji (ścieżka — zakres — właściciel), data następnego przeglądu.

Przykład: monorepo z pakietami `api`, `web`, `cli`; root 340 linii; agent 3× użył `console.log` w `cli` mimo reguły
w root. Higiena: wycięte 90 linii dublujących lint i opis katalogów → root 250. Sygnał (powtarzany błąd w module
z trzema przypadkami) → `packages/cli/CLAUDE.md`, 30 linii (punkt wejścia `src/main.ts`, logger `src/log.ts`,
zakaz globalnego `fetch`), reguły CLI usunięte z roota → root 190 linii + sekcja „Moduły z własnym CLAUDE.md”.
`api` i `web` zostają na szczeblu 1. Kontrola po tygodniu: 0 nowych `console.log` w 5 zadaniach w `cli`.
