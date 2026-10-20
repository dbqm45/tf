---
name: ddd-legacy-modernization
description: Użyj przy DDD na kodzie zastanym — słownik i rozjazdy model↔kod, agregat z niezmiennika, ACL.
metadata:
  przeglad: 2027-10-09
  katalog: "Użyj, gdy w działającym kodzie (po MVP, legacy) trzeba sprawdzić, czy odwzorowuje domenę, i zaplanować modernizację — destylacja słownika z dokumentów i kodu z tabelą rozjazdów model↔kod, subdomeny, kandydaci na agregaty ze statusem niezmiennika; wybór niezmiennika (rdzeniowość × rozsmarowanie × egzekwowanie) i projekt agregatu-strażnika; wykrycie przeciekającej zależności i projekt ACL (obiekt wartości, wąski port, adapter) ze sprawdzalnym kryterium „pakiet tylko w katalogu adaptera” egzekwowanym regułą dependency-cruiser / ESLint / ArchUnit. Wynik to diagnozy i plany, nie kod produkcyjny. Nie do warsztatu z ekspertami (ddd-facilitation, ddd-event-storming), projektu modelu od zera (ddd-tactical-design), relacji między kontekstami (ddd-context-mapping) ani refaktoryzacji struktury bez zmiany pojęć (eng-refactor-planning)."
  slowa: "legacy DDD, DDD w istniejącym kodzie, modernizacja legacy, kod nie odpowiada domenie, destylacja domeny, słownik z kodu, rozjazd model kod, PRD a kod, to samo słowo znaczy kilka rzeczy, niezmiennik tylko w UI, reguła rozsmarowana, agregat strażnik, przeciekająca zależność, biblioteka wszędzie, typy biblioteki w API, ACL dla biblioteki, wymiana biblioteki, izolacja zależności"
---

# DDD na kodzie zastanym — destylacja, niezmiennik, ACL

Refaktoryzacja pyta „jak bezpiecznie zmienić kod”. Ten skill pyta **„czy kod odpowiada temu, jak działa biznes”**.
Produkt to trzy diagnozy z planami — nie kod produkcyjny. Nazw bytów, niezmienników ani przecieków **nie zakładasz
z góry**: odkrywasz je z dokumentów i kodu, cytując `plik:linia`, które naprawdę sprawdziłeś.

## Kiedy (sygnały, że domena boli)
- to samo słowo znaczy kilka rzeczy (trzy różne „Account”: profil, rachunek, konto księgowe);
- byt z PRD nie ma odpowiednika w kodzie albo żyje jako luźny identyfikator przy wierszach;
- dane regularnie wpadają w „niemożliwy” stan i ratuje je skrypt;
- wymiana jednej biblioteki to projekt na sprint.
Przed walidacją produktu (MVP) zwykle za wcześnie — wiedza o domenie jest jeszcze płytka; modelujesz, gdy boli.

## Krok 0 — kontekst (wspólny dla A–C)
PRD, decyzja o stacku, README, historia zmian w `docs/project/`. Brak dokumentów wymagań → README + kod, zapisane
jako ograniczenie. Ustal, gdzie żyje logika (API / serwis / domena / UI / persystencja) i listę zależności z manifestu.
Mapa kodu (eng-codebase-mapping) skraca ten krok.

## A. Destylacja domeny → `docs/project/02-domain/distillation.md`
1. **Słownik:** pojęcie · definicja · źródło (`plik:linia` dokumentu) · gdzie w kodzie (`plik:linia`) albo
   **„BRAK w kodzie”**. Wszystkie nazwy tego samego bytu (baza, UI, odpowiedź API, mowa zespołu) w jednym wierszu.
2. **Subdomeny** core / supporting / generic z uzasadnieniem w celach produktu (ddd-strategic-analysis).
3. **Kandydaci na agregaty** + niezmiennik (cytat) + status: **egzekwowany / deklarowany / ignorowany**.
4. **Rozjazdy model ↔ kod** (najcenniejsza część): dokument mówi X · kod robi Y · dowód.
5. **Ranking:** wartość (jak rdzeniowy niezmiennik) × ryzyko (jak słabo egzekwowany) → #1 do dalszej pracy.
Nowe wpisy słownika trafiają do `glossary.md` jako **propozycje** do akceptacji człowieka (ddd-facilitation).

## B. Niezmiennik → agregat-strażnik → `docs/project/02-domain/invariant-<nazwa>.md`
1. Lista reguł „zawsze prawdziwych” z dokumentów i kodu: „X powstaje tylko z Y”, „A→B wymaga C”, „Z jest atomowe”,
   „D nigdy nie jest zapisywane”.
2. Trzy osie dla każdej: **rdzeniowość** (cele produktu) · **rozsmarowanie** (ile plików i warstw) ·
   **egzekwowanie** (egzekwowany / deklarowany / naruszalny). Wybierz najbardziej rdzeniowy i najsłabiej
   egzekwowany — często nie ten, który podejrzewasz.
3. **Diagnoza** z `plik:linia` we wszystkich warstwach: gdzie reguły brak, gdzie jest niespójna, gdzie UI jest
   jedynym strażnikiem, gdzie endpoint ufa danym z żądania, gdzie błąd jest logowany i połykany.
4. **Projekt** (ddd-tactical-design): korzeń agregatu jako **jedyne** miejsce egzekwowania; metody z warunkami
   wstępnymi; nielegalna operacja rzuca **nazwany błąd domenowy** (fail-fast, nie „zaloguj i jedź dalej”);
   repozytorium ładuje i zapisuje całość; niezmiennik wymagający atomowości → jedna transakcja; cienka trasa API:
   parsuj wejście → metoda agregatu → mapowanie błędu na odpowiedź; egzekwowanie z klienta przenosi się na serwer.
5. **Before/after** dla każdego dzisiejszego miejsca reguły, fazy (test-first, eng-behavior-preserving-refactoring),
   przypadki testowe legalnych i nielegalnych operacji.

## C. Przeciek zależności → ACL → `docs/project/02-domain/acl-<pakiet>.md`
1. **Sygnały przecieku:** ten sam pakiet w API + UI + serwisie; typy biblioteki w sygnaturach domeny lub w DTO
   i odpowiedziach; ta sama konwersja obiektu biblioteki w kilku miejscach; SDK wołane po obu stronach granicy
   klient/serwer. Dla każdej zależności: **wszystkie** pliki, które ją znają (`rg -l "from '<pakiet>'"`,
   ast-grep dla importów dynamicznych).
2. **Osie:** liczba warstw i plików · koszt wymiany dziś · czy dokumenty deklarowały wymienialność. Rozjazd
   intencji i kodu („miało dać się wymienić”) to najmocniejszy sygnał. Wybierz najgorszy przeciek.
3. **Diagnoza:** duplikaty, przecieki granic, szczególnie **biblioteka serwerowa w paczce klienta**.
4. **Projekt:** obiekt wartości domeny jako jedyne miejsce wiedzy o kształcie zależności (mapowanie z i do
   persystencji, konwersja z i do typu biblioteki) · **wąski port** w języku domeny · **adapter** owijający
   bibliotekę. Reszta kodu zna tylko port; UI dostaje dane domenowe, nie obiekt biblioteki. Decyzje zależne od
   kontraktu biblioteki rozstrzygasz z jej dokumentacji i kodujesz w ACL, nie w API.
5. **Dowód izolacji:** lista „zna dziś / zna po refaktorze”.
6. **Kryterium ukończenia (sprawdzalne poleceniem):** wyszukanie nazwy pakietu zwraca **wyłącznie pliki katalogu
   adaptera**. Utrwalasz je regułą w CI — dependency-cruiser `forbidden`, ESLint `no-restricted-imports`, ArchUnit;
   gotowe szablony: `references/szablony-regul.md`.

## Dalej
Artefakty A–C są wejściem do planowania kroku (core-plan-interview → plan z fazami). Hot spoty z Event Stormingu
(ddd-event-storming) to kandydaci na kolejne kroki. Cykl: odkryj → nazwij rozjazdy → zabezpiecz niezmiennik →
odizoluj zależność → zaplanuj. Szablony dokumentów A–C: `references/szablony-dokumentow.md`.

## Przykład
**Sytuacja:** aplikacja do fiszek po MVP; PRD opisuje „sesję generacji” z cyklem życia.
**Wynik:**
- A: w kodzie sesja to tylko luźny identyfikator przy wierszach propozycji (BRAK bytu); propozycja ma cztery nazwy
  w czterech warstwach. Rozjazd: PRD „sesja finalizuje się po rozstrzygnięciu wszystkich propozycji” — kod pozwala
  zapisać fiszki bez rozstrzygnięcia reszty (`src/api/flashcards.ts:41`).
- B: niezmiennik #1 (rdzeniowy, pilnuje go tylko licznik w UI) → agregat `GenerationSession` z `accept()`,
  `reject()`, `finalize()`; `finalize()` przy nierozstrzygniętej propozycji rzuca `SessionHasUnresolvedProposals`;
  zapis w jednej transakcji; trasa API tylko mapuje błąd na 409.
- C: typ `Card` biblioteki harmonogramu powtórek w schemacie bazy, w odpowiedzi API i w propsach komponentu
  (7 plików, 3 warstwy; PRD deklarował wymienialny algorytm) → obiekt wartości `ReviewSchedule`, port `Scheduler`,
  adapter `src/scheduling/adapter/`. Kryterium: `rg -l "from 'ts-fsrs'"` zwraca tylko pliki adaptera; reguła
  `forbidden` w dependency-cruiser w CI.

## Checklista
- [ ] nic nie założone z góry; każde pojęcie z cytatem i statusem w kodzie (`plik:linia` albo „BRAK w kodzie”)
- [ ] tabela rozjazdów model ↔ kod; wpisy słownika jako propozycje
- [ ] wybór niezmiennika i przecieku uzasadniony na osiach, z diagnozą we wszystkich warstwach
- [ ] projekt: jedyne miejsce egzekwowania, nazwany błąd, transakcja, cienka trasa; port + adapter + obiekt wartości
- [ ] kryterium ACL sprawdzalne poleceniem i utrwalone regułą; plany bez kodu produkcyjnego

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 4, lekcja 5 (modernizacja legacy z DDD) i trzy prompty do niej (destylacja,
  niezmiennik → agregat, ACL) — materiał szkoleniowy (dostęp 2026-10-09); opisane własnymi słowami.
- E. Evans, *Domain-Driven Design* (2003) — agregat, Anti-Corruption Layer, język wszechobecny.
- Składnia reguł sprawdzona 2026-10-10: dependency-cruiser 18.5.0 (`forbidden` z `from.pathNot` / `to.path`),
  ESLint 9.39.1 (`no-restricted-imports` w konfiguracji płaskiej z wyjątkiem dla katalogu adaptera).
