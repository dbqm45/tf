# Eksport danych (CSV, XLSX) z API

Eksport wygląda jak drobna funkcja („pobierz CSV”), ale przy dużych zbiorach staje się zadaniem w tle, kanałem
wycieku danych i wektorem ataku na arkusz kalkulacyjny odbiorcy.

## 1. Synchronicznie czy w tle
- **Synchronicznie** tylko dla małych zbiorów z twardym limitem (np. do 10 tys. wierszy): odpowiedź strumieniowana
  (`Content-Disposition: attachment`), bez budowania całego pliku w pamięci.
- **W tle** powyżej limitu:
  - `POST /exports` z filtrem i formatem odpowiada `202 Accepted` z zasobem zadania (`Location: /exports/{id}`);
  - zasób zadania ma status (`queued` / `running` / `done` / `failed`), postęp i wynik;
  - po zakończeniu powiadomienie (w aplikacji, e-mail, webhook) zamiast odpytywania co sekundę.
- Żądanie eksportu ma klucz idempotencji. Ponowne kliknięcie nie uruchamia drugiego zadania (`SKILL.md`,
  „Idempotencja”).
- Limit liczby równoczesnych eksportów na użytkownika i na organizację. Duże eksporty idą w osobnej kolejce, żeby
  nie zablokowały zwykłych zadań.

## 2. Te same filtry i uprawnienia co lista
- Eksport przyjmuje **ten sam filtr** co endpoint listy (`GET /customers?...`) i przechodzi przez tę samą
  autoryzację, zawsze po stronie serwera. Rekordy, których użytkownik nie widzi na liście, nie trafiają do pliku.
- Uprawnienie do eksportu jest osobne od uprawnienia do przeglądania. Pobranie całej bazy klientów to inna
  operacja niż obejrzenie jednego rekordu.
- Spójna migawka: zadanie czyta w jednej transakcji tylko do odczytu albo względem stałego momentu
  (`as_of = czas zlecenia`) i kursora po unikalnym kluczu. Inaczej rekordy zmienione w trakcie trafią do pliku
  dwa razy albo wcale.

## 3. Plik i jego cykl życia
- Plik w magazynie obiektów, pobierany przez **podpisany link z krótkim czasem ważności** (np. 15 min do 24 h),
  wydawany dopiero po ponownym sprawdzeniu, że pobierający to zlecający albo ma uprawnienie.
- Plik wygasa i jest usuwany automatycznie (np. po 7 dniach). To część polityki retencji danych.
- Duże pliki: kompresja albo podział na części, a w nazwie data i filtr
  (`klienci_status-active_2026-11-10.csv`).

## 4. Dane osobowe i kolumny
- Eksportujesz tylko kolumny potrzebne do celu. Lista kolumn jest jawna (allowlista), bez „wszystkich pól
  encji”. Pola wrażliwe (PESEL, IBAN, notatki) tylko za osobnym uprawnieniem albo zamaskowane. Klasy danych:
  arch-privacy-compliance (pack-it).
- Każdy eksport zapisujesz w audit logu: kto, kiedy, jaki filtr, ile wierszy, które kolumny. Plik z danymi
  osobowymi to częste źródło wycieku (be-business-app-patterns, pack-it).

## 5. Wstrzykiwanie formuł do CSV (CSV injection)
- Komórka zaczynająca się od `=`, `+`, `-`, `@`, tabulatora albo powrotu karetki może zostać wykonana jako formuła
  po otwarciu pliku w arkuszu kalkulacyjnym. Przykład: nazwa firmy `=HYPERLINK("http://…")` wpisana przez klienta.
- Wartości pochodzące od użytkowników neutralizujesz przy eksporcie: poprzedzasz apostrofem (`'`), gdy zaczynają
  się od jednego z tych znaków, i zawsze ujmujesz pole w cudzysłów z podwojeniem cudzysłowów wewnątrz.
  [niezweryfikowane w źródle 2026-11-10: OWASP „CSV Injection” — strona niedostępna z tego środowiska]
- Liczby i daty z bazy formatujesz jawnie (separator dziesiętny, ISO 8601) i podajesz kodowanie (UTF-8 z BOM,
  jeśli odbiorcą jest Excel).

## 6. Testy
- Eksport z filtrem zawiera dokładnie te rekordy co lista z tym filtrem dla tego samego użytkownika.
- Użytkownik bez uprawnienia nie zleci eksportu i nie pobierze cudzego pliku, nawet znając jego identyfikator.
- Wartość `=1+1` w danych trafia do pliku jako tekst.
- Link wygasa, a plik znika po terminie retencji.
- Ponowione żądanie z tym samym kluczem idempotencji zwraca to samo zadanie.
