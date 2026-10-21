# Techniki rozplątywania modelu

Cztery techniki na model, w którym ta sama wiedza siedzi w wielu miejscach, relacje się rozjeżdżają, a każda nowa
potrzeba kończy się kolejną wartością pola „status”.

## 1. Jedno źródło prawdy (single source of truth)
- **Zasada:** każdy fakt biznesowy ma jednego właściciela (agregat w jednym kontekście). Pozostali wskazują go
  identyfikatorem albo trzymają kopię do odczytu, odświeżaną zdarzeniem (read model). Kopia nigdy nie jest
  podstawą decyzji, która ten fakt zmienia.
- **Test:** „gdzie zmienię ten fakt, gdy zmieni się w biznesie?”. Więcej niż jedno miejsce oznacza, że fakt jest
  rozplątany źle.
- **Sygnały:**
  - ta sama lista identyfikatorów po obu stronach relacji;
  - pola „skopiowane dla wygody” bez zdarzenia, które je odświeża;
  - dwie tabele z tą samą datą ważności;
  - spory zespołów „u kogo jest prawda”.
- **Procedura:**
  1. Wypisz fakty, które się rozjeżdżają.
  2. Dla każdego ustal właściciela: kto o nim decyduje w biznesie.
  3. Pozostałe kopie zamień na odwołania albo read modele.
  4. Zmianę faktu ogłaszaj zdarzeniem (ddd-tactical-design, ddd-context-mapping).

## 2. Ukryte pojęcie w relacji wiele do wielu
- **Zasada:** relacja wiele do wielu między dwoma pojęciami prawie zawsze kryje trzecie pojęcie. Ma ono własne
  dane (daty od–do, warunki, rola), własny cykl życia i własne reguły. Nazwij je językiem biznesu. Staje się
  jedynym źródłem prawdy o relacji.
- **Przykład:** lekarz ↔ przychodnia to **Zatrudnienie** (od–do, wymiar etatu, specjalizacja w tej przychodni,
  grafik). Z kolei student ↔ kurs to **Zapis** (termin, status zaliczenia, ocena). Listy identyfikatorów po obu
  stronach znikają, a pytanie „gdzie pracuje lekarz w dniu X” ma jedno miejsce odpowiedzi.
- **Pytania do eksperta:**
  - „Co się dzieje, gdy ta relacja się zaczyna i kończy?”
  - „Czy relacja ma daty, warunki albo dokument?”
  - „Czy ta sama para może być powiązana dwa razy w różnych okresach?”

  Każde „tak” potwierdza, że relacja jest osobnym pojęciem.
- **Archetyp:** relacje między stronami to PartyRelationship
  (`.claude/skills/ddd-archetypes/references/party.md`), a umowa z pozycjami to Agreement
  (`.claude/skills/ddd-archetypes/references/agreement.md`).

## 3. Status to nie mechanizm rozszerzania
- **Problem:** każda nowa potrzeba dostaje nową wartość statusu, np. oferta jako „zamówienie ze statusem oferta”,
  „VIP”, „zamówienie hurtowe”. Kończy się to rozlanymi warunkami `if (status == …)` i regułami, które obowiązują
  tylko dla części wartości.
- **Status jest w porządku**, gdy opisuje cykl życia jednego pojęcia z jawnymi przejściami (maszyna stanów):
  te same dane, inne dozwolone operacje.
- **Zamiast nowej wartości statusu:**
  - inne dane, reguły i cykl życia oznaczają **osobne pojęcie** (Becoming: oferta przechodzi w umowę albo
    zamówienie, ale nią nie jest);
  - ten sam byt w nowym kontekście to **rola** (Role Object, eng-design-patterns);
  - dodatkowa zdolność dla części obiektów to **rozszerzenie** (Extension Object, eng-design-patterns);
  - inny sposób liczenia to **polityka** (ddd-tactical-design).

## 4. Dwa poziomy modelu: wiedza i operacje
- **Poziom wiedzy (knowledge level):** typy, reguły i konfiguracja, które biznes definiuje i zmienia, np. rodzaj
  ubezpieczenia z polami i regułami, typ produktu, procedura, plan kont, uprawnienia ról.
- **Poziom operacji (operations level):** konkretne zdarzenia i egzemplarze tworzone na co dzień, np. polisa,
  egzemplarz produktu, wykonana czynność, księgowanie. Każdy z nich wskazuje swój typ z poziomu wiedzy.
- **Kiedy:** biznes chce dodawać rodzaje bez programisty, reguły zależą od rodzaju, a rodzajów przybywa.
- **Zasady:**
  - Operacje odwołują się do wiedzy, nigdy odwrotnie.
  - Zmiana wiedzy to nowa wersja. Nowe operacje używają nowej wersji, istniejące zostają przy swojej (agreement,
    pricing w ddd-archetypes).
  - Poziom wiedzy ma własne reguły poprawności, np. nie usuniesz typu, który ma operacje.
- **Koszt:** model staje się abstrakcyjny i trudniejszy do czytania. Gdy rodzajów jest kilka i rzadko przybywa,
  wystarczą zwykłe klasy.
- **W archetypach:** ProductType i ProductInstance (`product.md`), procedura i czynność (`activity-process.md`),
  typ i egzemplarz zasobu (`resource-service.md`).

## Źródła
- M. Fowler, *Analysis Patterns: Reusable Object Models*, Addison-Wesley, 1996 [niezweryfikowane: rok według
  katalogów 1996, część wydań podaje 1997]. Poziom wiedzy i operacji: rozdz. 2 „Accountability”, sekcja
  „Accountability Knowledge Level” (spis treści u wydawcy, InformIT, odczyt 2026-10-21).
- E. Evans, *Domain-Driven Design: Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, rozdz. 16
  „Large-Scale Structure”, wzorzec „Knowledge Level” [niezweryfikowane: według spisu treści ze źródeł wtórnych].
- J. Arlow, I. Neustadt, *Enterprise Patterns and MDA: Building Better Software with Archetype Patterns and UML*,
  Addison-Wesley, ISBN 9780321112309, rok: źródła podają 2003 lub 2004 (rozdziały Party, Product, Inventory, Rule według spisu treści).
- Techniki 1–3 opisano własnymi słowami na podstawie powyższych źródeł i programu szkolenia „DDD — zaawansowane
  techniki modelowania i archetypy” (Bottega IT Minds, materiał od człowieka, 2026-10-21).
