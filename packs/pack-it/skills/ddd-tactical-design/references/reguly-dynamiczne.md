# Reguły dynamiczne, zmienne w czasie i zależne od historii

Gdy agregat i jedna polityka (strategia) nie wystarczają, bo reguły składają się z części, zmieniają się co rok,
definiuje je biznes albo zależą od tego, co działo się wcześniej.

## 1. Polityka jako funkcja i kompozycja polityk
- **Polityka** to czysta funkcja `(kontekst) → wynik`, np. rabat, kara, limit albo decyzja tak/nie z uzasadnieniem.
  Nie zapisuje stanu i nie robi wejścia/wyjścia (ddd-tactical-design: Decider).
- **Kompozycja:** małe polityki łączysz w większe:
  - **łańcuch:** kolejne kroki przetwarzają wynik albo decydują, kto obsłuży przypadek (łańcuch zobowiązań,
    eng-design-patterns);
  - **drzewo:** węzły `I`, `LUB`, `NIE`, „pierwsza pasująca”, „suma”, „minimum” i liście z regułami prostymi.
    Specyfikacja z łączeniem `and`/`or`/`not` to drzewo reguł tak/nie;
  - **dekorator polityki:** opakowanie, które zmienia wynik innej polityki bez jej zmiany, np. limit rabatu do
    30%, zaokrąglenie, zapis uzasadnienia, wyjątek dla wybranego klienta (supple design).
- **Fabryka polityk:** buduje drzewo z konfiguracji (poziom wiedzy, ddd-deep-modeling). Biznes zmienia regułę
  danymi, a kod zna tylko klocki i sposoby ich łączenia.
  - Konfiguracja ma własną walidację: znane klocki, poprawne typy, brak cykli.
  - Konfiguracja ma wersję.
- **Wynik z uzasadnieniem:** każda polityka zwraca nie tylko wartość, ale też powód („rabat 10%: klient powyżej
  2 lat; limit 30%”). Bez tego reguł zbudowanych z danych nie da się wyjaśnić ani przetestować.
- **Granica:** drzewo z kilkunastu klocków jest w porządku. Gdy biznes zaczyna „programować” w konfiguracji
  (pętle, zmienne, wywołania zewnętrzne), potrzebny jest silnik reguł albo DSL. To decyzja architektoniczna (ADR).

## 2. Scoring
- **Scoring** to polityka, która zamienia cechy przypadku na liczbę punktów. Liczbę porównuje się z progami
  decyzji, np. ocena ryzyka, priorytet zgłoszenia, kolejność leadów.
- **Budowa:** lista składników (cecha → punkty, każdy jako mała polityka), funkcja łącząca (suma, ważona suma,
  minimum), progi decyzji i uzasadnienie (które składniki dały ile punktów).
- **Zasady:**
  - Składniki i progi są wersjonowane, bo zmieniają się częściej niż kod.
  - Decyzja zapisuje wersję scoringu i rozbicie punktów (audyt, spory, odwołania).
  - Gdy wagi powstają z danych (model statystyczny lub ML), to już inna dziedzina: ai-research-methods,
    data-analysis.

## 3. Reguły zmienne w czasie
- **Reguła ma okres obowiązywania.** Sprawy rozliczasz według reguły obowiązującej w dniu istotnym dla sprawy
  (data zdarzenia, zawarcia umowy, zgłoszenia), a nie w dniu obliczenia. Datę istotną ustala ekspert domeny.
- **Kopiowanie kodu jako wzorzec:** nowa wersja reguły to nowa klasa albo funkcja (`KaryRegulamin2025`,
  `KaryRegulamin2026`) i wpis w rejestrze „od kiedy obowiązuje”. Nie dokładasz warunków `if (rok >= 2026)`
  w starej klasie.
  - Stara wersja zostaje nietknięta: stare sprawy liczą się tak samo jak wtedy, a testy starej wersji dalej
    przechodzą.
  - Zduplikowany kod jest tu świadomym wyborem, bo wersje to osobne fakty prawne. Gdyby je współdzielić, zmiana
    jednej mogłaby zmienić drugą.
- **Wybór wersji:** jedno miejsce, np. rejestr polityk albo fabryka, wybiera wersję po dacie istotnej. Wersja
  trafia do wyniku i zdarzenia.
- **Dwie osie czasu:** gdy liczy się też, kiedy system się dowiedział (korekty wsteczne, aneksy z datą
  wcześniejszą), stosujesz dwa zakresy dat (ddd-archetypes, `.claude/skills/ddd-archetypes/references/agreement.md`).

## 4. Reguły zależne od historii zdarzeń
- **Problem:** decyzja zależy od sekwencji wcześniejszych zdarzeń, nie tylko od bieżącego stanu. Przykłady:
  „trzecia reklamacja w roku”, „po dwóch nieudanych płatnościach blokada”, „rabat, jeśli klient wrócił po
  porzuceniu koszyka”.
- **Rozwiązanie:** stan potrzebny regule to złożenie (fold) strumienia zdarzeń: `stan = zdarzenia.reduce(evolve)`.
  Reguła działa na tym stanie.
  - W modelu Decider: `decide(stan, komenda)` i `evolve(stan, zdarzenie)`.
  - Z event sourcingiem strumień jest źródłem prawdy. Bez niego trzymasz w agregacie tylko to, czego reguła
    potrzebuje (np. licznik z datami).
- **Zasady:**
  - Stan dla reguły jest minimalny: nie cała historia, tylko to, co reguła czyta.
  - Kolejność zdarzeń jest częścią reguły, więc testy podają sekwencję (Given: zdarzenia, When: komenda,
    Then: zdarzenia albo odrzucenie).
  - Nowa reguła na starej historii to migracja danych albo nowa projekcja.

## 5. Agregat jako maszyna stanów
- **Kiedy:** zestaw dozwolonych operacji zależy od etapu cyklu życia, np. zamówienie złożone, opłacone, wysłane,
  anulowane.
- **Budowa:**
  - Stan to jawny typ (wyliczenie albo osobne klasy stanów).
  - Każda metoda biznesowa sprawdza przejście w jednym miejscu (tabela przejść albo metoda stanu).
  - Udane przejście emituje zdarzenie.
  - Niedozwolone przejście to odrzucenie z powodem, a nie cichy brak zmiany.
- **Warianty:**
  - mało stanów i prosta logika: wyliczenie z tabelą przejść;
  - stany z różnymi danymi i zachowaniem: osobne typy stanów (wzorzec State, eng-design-patterns), np.
    `ZamówienieOpłacone` ma numer płatności, a `ZamówienieZłożone` go nie ma.
- **Pułapka:** stan nie zastępuje osobnych pojęć. Gdy „stan” ma inne dane, reguły i właściciela, to inne pojęcie
  (ddd-deep-modeling, `.claude/skills/ddd-deep-modeling/references/rozplatywanie.md`).

## Źródła
- E. Evans, *Domain-Driven Design*, Addison-Wesley, 2003, rozdz. 10 „Supple Design” (m.in. Intention-Revealing
  Interfaces, Side-Effect-Free Functions, Closure of Operations, Declarative Design) oraz specyfikacja
  [niezweryfikowane: według spisu treści u wydawcy, bez lektury tekstu w tej sesji].
- E. Evans, M. Fowler, „Specifications”, PLoP 1997 — kompozycja specyfikacji (`and`, `or`, `not`)
  [niezweryfikowane: streszczenie ze źródeł wtórnych].
- E. Gamma, R. Helm, R. Johnson, J. Vlissides, *Design Patterns*, Addison-Wesley, 1994, ISBN 0201633612 —
  Decorator, Chain of Responsibility, State, Strategy.
- M. Fowler, „Temporal Patterns” (martinfowler.com/eaaDev/timeNarrative.html): Effectivity, Temporal Property,
  Temporal Object [niezweryfikowane: strona niedostępna z tej sesji].
- M. Fowler, „Event Sourcing” (martinfowler.com/eaaDev/EventSourcing.html) [niezweryfikowane: strona
  niedostępna z tej sesji].
- „Kopiowanie kodu jako wzorzec”, fabryki polityk i scoring opisano własnymi słowami na podstawie programu
  szkolenia „DDD — zaawansowane techniki modelowania i archetypy” (Bottega IT Minds, materiał od człowieka,
  2026-10-21).
