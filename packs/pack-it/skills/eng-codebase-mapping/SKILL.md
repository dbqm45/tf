---
name: eng-codebase-mapping
description: Użyj przy nieznanym kodzie i ocenie wpływu zmiany — punkty wejścia, warstwy z importów, węzły centralne, cykle.
metadata:
  przeglad: 2027-10-09
  katalog: "Użyj, gdy trzeba zrozumieć nieznany kod lub ocenić wpływ zmiany — punkty wejścia, warstwy z grafu importów, węzły centralne i cykle runtime vs leniwe (scripts/code_graph.py dla Pythona, TS/JS, Javy, C# i Go), terytorium z historii gita (zmiany w czasie, współzmiany, kontrybutorzy, hotspoty — scripts/git_territory.py), legenda modułów, trasa czytania dla nowej osoby, wpływ diffu (1 krok w górę i w dół, warstwy, ryzyko), pewność krawędzi, analiza jednego przepływu i badanie kodu pod zmianę (research.md). Nie do oceny długu (eng-tech-debt-audit), wyboru refaktoryzacji (eng-refactor-planning) ani projektowania granic (ddd-strategic-analysis)."
  slowa: "graf importów bez narzędzi, cykle importów, nieznane repo, mapa kodu, mapa repo, od czego zacząć czytać, punkty wejścia, graf zależności, historia gita, co się najczęściej zmienia, współzmiany, kto zmieniał, kogo zapytać, hotspoty, analiza przepływu, jak działa ten feature, research przed zmianą, wpływ zmiany"
---

# Mapa kodu

Najpierw mapa, potem czytanie. Agent, który zaczyna od losowych plików, zużywa kontekst i myli peryferie z rdzeniem.
Mapę budujesz z narzędzi deterministycznych, a model językowy tylko nazywa i opisuje to, co narzędzia pokazały.

**Szeroki skan, potem pogłębienie.** Mapa repo to szeroki, płytki skan z CLI — może go robić tańszy model, bo
narzędzia pracują poza kontekstem. Pogłębienie jednego przepływu to osobne zadanie z mapą jako wejściem
(`references/analiza-przeplywu.md`). Nie łącz w jednym poleceniu szukania struktury, wyboru ważnych obszarów
i rozumienia zachowania — „przeczytaj całe repo” daje płaskie streszczenie bez priorytetów. Drzewo katalogów
to hipoteza: nie pokazuje, co się zmienia, co pęka razem ani co jest martwe.

## Procedura
1. **Inwentarz:** liczba plików i linii per katalog/projekt, języki, frameworki. README i manifesty traktujesz jako
   wskazówki, nie prawdę — kod jest źródłem. Przy dużym repo (> ~100 plików w zakresie) uzgodnij zakres z człowiekiem.
1a. **Terytorium z historii (okno 12 mies.)** — **uruchom** `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --all`
   (`--json`, `--depth 3`, gdy wynik zbyt ogólny, np. `src/backend`):
   - top 10 katalogów i plików wg liczby commitów, bez szumu (lockfile'e, snapshoty, generowane, tłumaczenia, `.env*`);
   - ten sam ranking per kwartał — stałe centrum odróżnia od jednorazowej kampanii zmian;
   - współzmiany: pary katalogów i plików z tych samych commitów (commity > 30 plików pominięte — masowy refaktor
     skleja niezwiązane pliki); osobno **huby** zmieniane z wieloma obszarami (konfiguracja, tłumaczenia, kod generowany);
   - pliki z rankingu, których nie ma w `git ls-files`, są oznaczone — historia mówi o przeszłości;
   - hotspoty: zmiany × linie niepuste (eng-tech-debt-audit).
1c. **Spis i konwencje bez modelu** (duże lub obce repo): `python3 .claude/skills/eng-codebase-mapping/scripts/repo_inventory.py
   <repo> [--budget-tokens N]` — języki, pliki budowania, wykluczenia (zależności, build, kod wygenerowany), moduły
   i partie plików w budżecie tokenów do analizy porcjami; `scripts/standards_scan.py <repo>` — narzędzia
   z konfiguracji i konwencje policzone w kodzie (nazwy plików, testy, łapanie błędów, logowanie, TODO) z udziałem,
   przykładami `plik:linia` i wyjątkami. To dane do standardu, nie standard.
1b. **Kontrybutorzy** (opcjonalnie, dla 3–5 stref ryzyka): `git_territory.py --authors <ścieżka>` — bez botów
   i commitów, których autorem jest agent AI. To lista „kogo zapytać, które PR-y przeczytać”, nie właściciele: nie
   mówi, kto nadal pracuje ani czy tamte decyzje są aktualne. Wiedza w jednej osobie = ryzyko na mapie. W mapie
   tylko login lub inicjały i obszar, bez ocen ludzi.
2. **Graf zależności z narzędzi**, nie z czytania:
   - Nx: `nx graph --file=graph.json` (projekty i zależności), granice modułów z tagów (tool-nx);
   - TS/JS: `madge --json` / `madge --circular`, dependency-cruiser (`--collapse`, `--focus`, `--reaches`, `--metrics`);
     Java: `jdeps`, ArchUnit, moduły Maven/Gradle; inne języki i ślepe plamy narzędzi: `references/wide-scan.md`.
   - Python, TS/JS, Java, C# i Go bez tych narzędzi (brak instalacji, brak sieci): **uruchom**
     `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo>` (`--impact <plik>`, `--focus <ścieżka>`
     — importy przez granicę modułu, dwa `--focus` — szew pary; `--json`) zamiast
     pisać własny skaner — daje kroki 3 i 5 oraz dane do 4: punkty wejścia z punktacją, krawędzie między pakietami
     workspace, grupy z kierunkiem, pary pod prąd, huby bez barreli (re-eksportów), cykle runtime osobno od domykanych
     importami leniwymi (w funkcji, `TYPE_CHECKING`, `import type`, `import()`); grupę z > 40% plików sam rozbija
     o poziom niżej (`--group-depth N` wyłącza). Liczby bierz z wyniku; kod czytaj, by
     nazwać warstwy i sprawdzić wątpliwe miejsca (punkt wejścia z samej nazwy, cykl przez `__init__`). C#: `using`
     wiąże z każdym plikiem przestrzeni nazw (krawędzie zgrubne); Java: klasy z tego samego pakietu bez importu
     są niewidoczne; wejścia Javy, C# i Go rozpoznaje po `main` (`Program.cs`, `@SpringBootApplication`).
   - Sprzężenie runtime (DI, flagi, kolejki, webhooki, refleksja, dynamiczny import, codegen) graf pomija — wpisz je
     do `unknowns`; warstwa bez grafu to „nie objęte narzędziem”, nie „brak powiązań”.
3. **Punkty wejścia** — punktacja kandydatów:
   konwencjonalna nazwa (`main.ts`, `app.config.ts`, `*.routes.ts`, `Application.java`) +3 · w korzeniu lub poziom niżej +1 ·
   górne 10% liczby importów wychodzących +1 · dolne 25% importów przychodzących +1. Do tego trasy (routing), endpointy
   (kontrolery), handlery kolejek, zadania cykliczne — `code_graph.py` wypisuje je osobno jako wejścia z rejestrów
   (zadania Celery, komendy Django, schemat GraphQL, aplikacje i trasy HTTP, kontrolery i cron w Nest).
4. **Warstwy (3–10):** grupa plików gęsto importujących się nawzajem (gęstość importów wewnątrz > ~0,3) to spójna
   warstwa; grupa często importowana, a sama mało importująca, jest fundamentem; zależności powinny płynąć
   UI/API → usługi → dane/narzędzia. Strzałka pod prąd to ustalenie.
5. **Węzły centralne i cykle:** pliki/klasy o największej liczbie połączeń (po odfiltrowaniu barreli `index.ts`,
   typów i stałych) — tu zmiana ma największy zasięg; cykle importów wypisz zawsze, z rodzajem: runtime (pęka przy
   imporcie) czy domykany dopiero importem leniwym lub typem (sprzężenie, nie błąd ładowania).
6. **Trasa czytania (5–15 kroków):** od najlepszego punktu wejścia w głąb po grafie (najpierw szerzej, potem w dół);
   ściśle powiązane 2–5 plików to jeden krok. Każdy krok: co tu jest i dlaczego czytać to teraz.
7. **Legenda modułów** dla obszarów istotnych dla ryzyka zmiany: rola (core / supporting / peripheral) · głębokość
   (deep / shallow) · profil zmian (stable / volatile / seasonal) · zasięg (load-bearing / contained) · wrażliwość.
   Każda etykieta z dowodem; bez dowodu → `do weryfikacji` (szczegóły: `references/wide-scan.md`).
8. **Zapis:** `docs/project/04-architecture/codebase-map.md` z datą i commitem HEAD: (1) TL;DR 5–7 zdań + diagram
   warstw (Mermaid), (2) teren: rdzeń vs peryferia, aktywność w czasie, (3) realne powiązania (importy + współzmiany
   + cykle, ze źródłem), (4) 4–6 stref ryzyka, każda z jednym „dlaczego”, (5) kogo zapytać (1–2 osoby na strefę),
   (6) pierwszy dzień: 5–8 plików, (7) ograniczenia: okno czasu, metoda, czego mapa NIE mówi. Wyniki robocze skanów
   obok (`codebase-map/territory.md`, `structure.md`); mapa to synteza, nie kopia tabel. Cel: nowa osoba po ~15 min
   wie, gdzie co żyje, co jest groźne i od czego zacząć.

## Pewność krawędzi
Każde połączenie na mapie ma etykietę: **WYCIĄGNIĘTE** (z narzędzia/AST), **WYWNIOSKOWANE** (z nazw, konwencji,
konfiguracji DI) albo **NIEPEWNE**. Połączeń nie zmyślasz; niepewne pokazujesz, a nie pomijasz.

## Wpływ zmiany (diff)
1. Zmienione pliki: `git diff --name-only <baza>...HEAD`.
2. **Świeżość mapy w monorepo:** `git diff --name-only <commit-mapy> HEAD -- <ścieżka-projektu>` — zmiany w innych
   projektach nie unieważniają mapy tego projektu. W Nx szybciej: `nx show projects --affected`.
3. Dla każdego pliku: zależności 1 krok w górę (kto go używa) i 1 krok w dół (czego używa), warstwy, które dotyka.
4. Ryzyko: złożoność pliku, liczba krawędzi między warstwami, zasięg (ile projektów/modułów) → niskie/średnie/wysokie.
5. Wynik do opisu PR: lista dotkniętych modułów, ryzyko, co przetestować (qa-regression).

## Badanie kodu pod zmianę (`research.md` kroku)
Gdy plan kroku wymaga wiedzy o istniejącym kodzie (wzorce, przepływ danych, punkty styku):
1. Sam przeczytaj pliki wskazane przez człowieka i lekcje projektu — zawężają, co warto badać.
2. Rozbij pytanie na 2–4 obszary; niejasny zakres → 1–3 pytania (zakres, głębokość, akcent). Wąskie pytanie → bez pytań.
3. Obszary równolegle: tani wykonawca szuka plików i wzorców, mocniejszy analizuje wiele plików; każdy wraca z `plik:linia`.
4. Zapis w `docs/project/<krok>/research.md` (jedyny plik, który badanie tworzy — kodu nie zmienia): data, commit,
   gałąź; Pytanie · Podsumowanie · Ustalenia (każde z `plik:linia`) · Wnioski architektoniczne · Kontekst historyczny
   · Otwarte pytania. Pytanie uzupełniające → sekcja „Badanie uzupełniające <data>” w tym samym pliku.
Brak `plik:linia` = brak twierdzenia. Wcześniejsze raporty i mapa to prior, nie prawda — nieaktualne twierdzenie
korygujesz jawnie. Badanie wewnętrzne odpowiada „co robi nasz kod”, nie „którą bibliotekę wybrać”
(core-source-research). Głęboka analiza jednego przepływu: `references/analiza-przeplywu.md`.

## Wyszukiwanie strukturalne
`rg` dla tekstu, ast-grep dla struktury (definicje, wywołania, sygnatury). Uruchamiaj binarkę `ast-grep`: na
Linuksie `sg` to zwykle polecenie zmiany grupy (`/usr/bin/sg`), a nie ast-grep. Każde zero z ast-grepa potwierdź
`rg` — zły wzorzec też daje zero. Tabela „które narzędzie na jakie pytanie”: `references/wide-scan.md`.

## Przykład
**Sytuacja:** „Gdzie zacząć czytać repo `shop` (Nx, Angular + NestJS)?”
**Wynik:** `nx graph` + `madge`; punkty wejścia `apps/api/src/main.ts` i `app.config.ts` (po 6 pkt), `app.routes.ts`
(4 pkt); warstwy kontroler → `order.service.ts` → repozytorium → `libs/db`; ustalenie: `libs/db/src/audit.ts`
importuje usługę (pod prąd, cykl — WYCIĄGNIĘTE); węzeł centralny `order.service.ts` (23 połączenia); krawędź przez
token DI — WYWNIOSKOWANE. `git_territory.py`: `apps/api/src/orders` zmieniany w każdym kwartale (stałe centrum),
para `orders` ↔ `libs/db/migrations` w 14 commitach, hub `libs/i18n`; dwa pliki z rankingu już usunięte. Strefa
ryzyka: zamówienia (load-bearing, volatile); kogo zapytać: 2 loginy. Trasa 7 kroków, mapa z datą i commitem.
Więcej przykładów: `references/przyklady.md`.

## Checklista
- [ ] graf z narzędzi, nie z domysłów; zakres uzgodniony przy dużym repo
- [ ] terytorium z historii: 12 mies., kwartały, współzmiany bez masowych commitów, istnienie plików sprawdzone
- [ ] legenda modułów z dowodem przy każdej etykiecie; sprzężenia runtime w `unknowns`
- [ ] punkty wejścia z punktacją, warstwy z kierunkiem zależności, cykle wypisane z rodzajem (runtime / leniwe)
- [ ] krawędzie z etykietą pewności
- [ ] trasa czytania 5–15 kroków; mapa z datą i commitem

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 4, lekcje 2–3 (mapa projektu z historii i grafu, analiza feature) i prompty do
  nich; moduł 2, lekcja 4 (badanie kodu pod zmianę) — materiał szkoleniowy (dostęp 2026-10-09); opisane własnymi słowami.
- dependency-cruiser 18.5.0 (`depcruise --help`, sprawdzone 2026-10-10): `--collapse`, `--focus`, `--focus-depth`,
  `--reaches`, `--metrics`, `--exclude`, `--do-not-follow`, `-T archi|mermaid|dot`; ast-grep 0.50.0; `/usr/bin/sg`
  w Ubuntu z pakietu `login` (sprawdzone 2026-10-10).
- Pomiar fabryki (odczyt 2026-10-18): pełna mapa ze `code_graph.py` vs własny skaner agenta na dwóch repozytoriach
  (TS ~22 tys. linii, Python ~860 tys.) — `docs/project/archive/research/20261018-code-graph.md`.

## Źródła inspiracji
[Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) (punktacja punktów wejścia, heurystyki warstw,
trasa czytania, wpływ diffu ze świeżością per ścieżka w monorepo) i [graphify](https://github.com/Graphify-Labs/graphify)
(węzły centralne, cykle, etykiety pewności krawędzi, „najpierw graf, potem grep”) — opisane własnymi słowami; zamiast
ich narzędzi fabryka używa `nx graph`, madge i jdeps.
