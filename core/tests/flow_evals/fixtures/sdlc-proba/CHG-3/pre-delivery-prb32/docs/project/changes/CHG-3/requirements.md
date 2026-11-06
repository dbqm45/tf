---
artifact: requirements
phase: requirements
status: proposed
version: 1
author: ewa
created: 2026-11-03
updated: 2026-11-03
inputs: [docs/project/changes/CHG-3/intent.md, docs/project/changes/CHG-3/decisions.md]
change: CHG-3
source: PRB-27
source_reported_at: 2026-11-03
---
# Wymagania zmiany CHG-3

## TL;DR
Strona główna pokazuje „Wdrożenia w ostatnich 7 dniach: N" za flagą `deploy_counter` (test: on, prod: off).
N to liczba wszystkich wdrożeń środowiska w oknie 7 × 24 h wstecz od chwili renderowania (UTC), także > 100.
Przy wyłączonej fladze strona jest bajt w bajt taka jak dziś. Ustalenia z bramek: CHG-3/D1 (DEC-0012), CHG-3/D2 (DEC-0013).

## Historia użytkownika
**US-01** — Odwiedzający widzi tempo wdrożeń
Jako odwiedzający stronę w środowisku z włączoną flagą `deploy_counter` widzę, ile wdrożeń tego środowiska było
w ostatnich 7 dniach, żeby ocenić tempo wdrożeń bez wołania `/deployments` i liczenia ręcznie.
Widoczność: każdy odwiedzający, bez dodatkowej autoryzacji (CHG-3/D2, DEC-0013).

## Ustalenia z bramek (nie do ponownego pytania)
| Kwestia | Ustalenie | Źródło |
|---|---|---|
| Okno | 7 × 24 h wstecz od chwili renderowania, UTC; ruchome, nie dni kalendarzowe | CHG-3/D2, DEC-0013 |
| Co liczymy | wszystkie wdrożenia środowiska, udane i nieudane; rozróżnienie poza zakresem | CHG-3/D2, DEC-0013 |
| Porażka | (a) liczba ≠ zapytanie do `deployments` dla tego samego env i okna (także > 100); (b) `deploy_counter` na prod `enabled: true` po wdrożeniu; (c) strona z flagą off inna niż dziś | CHG-3/D2, DEC-0013 |
| Widoczność | każdy odwiedzający tam, gdzie flaga on; start: test on, prod off; kontrola przez etapy rolloutu (faza plan) | CHG-3/D2, DEC-0013 |
| Wariant | A: render po stronie serwera, `countDeployments` w `src/deployments.js`, bez nowego endpointu | CHG-3/D2, DEC-0013 |

## Wymagania funkcjonalne

### FR-001 — Funkcja liczenia wdrożeń w oknie
`src/deployments.js` eksportuje `countDeployments(file, env, since)`, która zwraca liczbę wierszy `deployments`
dla `env` z `deployed_at` nie wcześniejszym niż `since` (porównanie przez `julianday`, jak w `LIST_SQL`, żeby formaty
`…:00Z` i `…:00.000Z` liczyły się poprawnie). Jedno zapytanie `COUNT`, bez stronicowania i bez limitu 100.
Brak pliku bazy = 0 (jak `listDeployments`). Baza otwierana tylko do odczytu.

**Kryteria akceptacji:**
- **E-01A** — okno i środowisko:
  ```
  wejście: env=test; wdrożenia test: now-1h, now-6d23h, now-7d1h; wdrożenie prod: now-1h; since = now-7d
  oczekiwany wynik: countDeployments(db, 'test', since) → 2
  ```
- **E-01B** — ponad 100 wdrożeń:
  ```
  wejście: 150 wdrożeń env=test w ciągu ostatnich 7 dni
  oczekiwany wynik: countDeployments(...) → 150 (a nie 100 ani 20)
  ```
- **E-01C** — mieszane formaty czasu:
  ```
  wejście: wdrożenia z deployed_at „2026-11-01T10:00:00Z" i „2026-11-01T10:00:00.000Z", oba w oknie
  oczekiwany wynik: oba zliczone → 2
  ```
- **E-01D** — brak pliku:
  ```
  wejście: file wskazuje nieistniejący plik
  oczekiwany wynik: 0, bez wyjątku
  ```
- **E-01E** — zgodność z bazą (kryterium porażki (a)):
  ```
  wejście: dowolny zestaw wdrożeń (w tym > 100) i okno 7 × 24 h
  oczekiwany wynik: wynik równy `SELECT COUNT(*) FROM deployments WHERE env = ? AND julianday(deployed_at) >= julianday(?)` wykonanemu wprost w teście
  ```
- **E-01F** — brzeg okna **[propozycja]**:
  ```
  wejście: wdrożenie dokładnie w chwili since
  oczekiwany wynik: liczone (granica dolna włącznie)
  ```

### FR-002 — Licznik na stronie za flagą
Gdy `deploy_counter` jest włączona dla odwiedzającego, `GET /` zawiera element
`<p data-flag="deploy_counter">Wdrożenia w ostatnich 7 dniach: N</p>`. N pochodzi z `countDeployments` dla
wybranego środowiska i `since` = chwila renderowania − 7 × 24 h (UTC). Okno liczone przy każdym żądaniu (bez cache).
Licznik jest w `<main>`, po akapicie „Środowisko". `renderPage` dostaje wartość już policzoną (np. `deployCount`);
sam nie czyta bazy.

**Kryteria akceptacji:**
- **E-02A** — flaga ON:
  ```
  wejście: flaga deploy_counter ON, 3 wdrożenia env w oknie
  oczekiwany wynik: GET / → 200, HTML zawiera „Wdrożenia w ostatnich 7 dniach: 3" w elemencie z data-flag="deploy_counter"
  ```
- **E-02B** — flaga OFF (kryterium porażki (c)):
  ```
  wejście: flaga deploy_counter OFF, baza z wdrożeniami
  oczekiwany wynik: GET / → 200, HTML identyczny bajt w bajt z wynikiem sprzed zmiany; istniejące testy strony przechodzą bez modyfikacji
  ```
- **E-02C** — zero wdrożeń:
  ```
  wejście: flaga ON, brak wdrożeń w oknie
  oczekiwany wynik: „Wdrożenia w ostatnich 7 dniach: 0" (licznik widoczny, nie ukryty)
  ```
- **E-02D** — ponad 100 na stronie:
  ```
  wejście: flaga ON, 150 wdrożeń w oknie
  oczekiwany wynik: HTML zawiera „…: 150"
  ```
- **E-02E** — flaga off nie dotyka bazy **[propozycja]**:
  ```
  wejście: flaga OFF, DEPLOYMENTS_DB wskazuje uszkodzony plik
  oczekiwany wynik: GET / → 200 (baza nie jest otwierana)
  ```

### FR-003 — Wybór środowiska
Środowisko licznika to `?env=` z listy `ENVIRONMENTS`; bez parametru — bieżące `APP_ENV` (`env` serwera).
Nieznana wartość `?env=` **[propozycja]**: strona nie zwraca błędu, tylko liczy dla domyślnego środowiska
(strona HTML nie powinna zależeć od parametru, którego nikt nie musi podawać). Etykieta pokazuje, dla którego
środowiska liczba jest policzona, tylko jeśli różni się od bieżącego — zob. pytanie P-01.

**Kryteria akceptacji:**
- **E-03A** — domyślne env:
  ```
  wejście: serwer env=test, GET / (bez ?env=), wdrożenia: 2 dla test, 5 dla prod, w oknie
  oczekiwany wynik: „…: 2"
  ```
- **E-03B** — jawne env:
  ```
  wejście: serwer env=test, GET /?env=prod, jak wyżej
  oczekiwany wynik: „…: 5"
  ```
- **E-03C** — nieznane env **[propozycja]**:
  ```
  wejście: serwer env=test, GET /?env=staging
  oczekiwany wynik: 200, licznik dla test (2), bez „staging" w HTML
  ```
- **E-03D** — eskapowanie (NF-001):
  ```
  wejście: GET /?env=<xss>
  oczekiwany wynik: 200, w HTML brak surowego „<xss>"
  ```

### FR-004 — Odporność na brak lub uszkodzenie bazy
Brak pliku bazy → licznik „0" (FR-001). Błąd odczytu (np. uszkodzona baza) przy włączonej fladze nie wywraca procesu:
obowiązuje istniejąca obsługa błędów serwera (500 `internal error`, szczegóły tylko w logu, `test/server-errors.test.js`).

**Kryteria akceptacji:**
- **E-04A** — brak pliku:
  ```
  wejście: flaga ON, DEPLOYMENTS_DB nie istnieje
  oczekiwany wynik: GET / → 200, „…: 0"
  ```
- **E-04B** — uszkodzona baza:
  ```
  wejście: flaga ON, DEPLOYMENTS_DB zawiera nie-SQLite
  oczekiwany wynik: GET / → 500 {"error":"internal error"}, proces działa dalej, treść błędu nie trafia do klienta
  ```

### FR-005 — Konfiguracja flagi
`config/flags.test.json` ma `deploy_counter: { "enabled": true, "rollout": 100 }`;
`config/flags.prod.json` ma `deploy_counter: { "enabled": false, "rollout": 0 }`. Włączenie na prod poza zakresem
tej fazy (etapy rolloutu: faza plan).

**Kryteria akceptacji:**
- **E-05A** — pliki flag:
  ```
  wejście: odczyt config/flags.test.json i config/flags.prod.json
  oczekiwany wynik: test → enabled true; prod → enabled false (kryterium porażki (b); test w repo pilnuje wartości prod)
  ```
- **E-05B** — brak regresji innych flag:
  ```
  wejście: te same pliki
  oczekiwany wynik: welcome_banner i show_last_deployed bez zmian
  ```

## Wymagania jakości
**NF-001 — Eskapowanie HTML (musi).** Każda wartość wstawiana do HTML (N, `env`) przechodzi przez `escape` z `src/page.js`.
Weryfikacja: E-03D.

**NF-002 — Brak regresji przy fladze off (musi).** Strona z `deploy_counter` off jest identyczna bajt w bajt jak
dziś; istniejące testy (`test/page.test.js`, `test/server.test.js`) przechodzą bez zmian. Weryfikacja: E-02B.

**NF-003 — Dokładność (musi).** N równa się wynikowi zapytania wprost do tabeli dla tego samego env i okna, także > 100.
Weryfikacja: E-01B, E-01E, E-02D.

**NF-004 — Wydajność (powinno).** Jedno zapytanie `COUNT` z użyciem indeksu `deployments_env_time (env, julianday(deployed_at))`;
brak dodatkowych zapytań na żądanie, gdy flaga off. Próg czasu strony: brak w zgłoszeniu i decyzjach — zob. P-02.
Weryfikacja: przegląd planu zapytania (`EXPLAIN QUERY PLAN` używa indeksu) **[propozycja]**.

**NF-005 — Bezpieczeństwo i ograniczenia (musi).** Brak nowych zależności (DL4, `node:sqlite`); CSP `default-src 'self'`
bez zmian (bez skryptów inline i JS klienta); `?env=` walidowane względem `ENVIRONMENTS`; zapytanie parametryzowane
(bez sklejania SQL). Brak dodatkowej autoryzacji (CHG-3/D2).

**NF-006 — Czas UTC (musi).** `since` liczony z zegara w UTC (`Date.now() − 7 × 24 h`), zapis ISO 8601 `Z`; funkcja
przyjmuje `since` jako argument, żeby test mógł zamrozić czas.

## Priorytety
| ID | Opis | Waga | Wydanie |
|---|---|---|---|
| FR-001 | `countDeployments` (okno, env, > 100, brak pliku) | musi | R1 |
| FR-002 | Licznik na stronie za flagą `deploy_counter` | musi | R1 |
| FR-005 | Flaga: test on, prod off | musi | R1 |
| FR-003 | Wybór środowiska `?env=` (domyślnie `APP_ENV`) | powinno | R1 |
| FR-004 | Odporność na brak/uszkodzenie bazy | musi | R1 |
| NF-001 | Eskapowanie HTML | musi | R1 |
| NF-002 | Strona bajt w bajt przy fladze off | musi | R1 |
| NF-003 | Dokładność względem bazy | musi | R1 |
| NF-004 | Wydajność (indeks, 1 zapytanie) | powinno | R1 |
| NF-005 | Bezpieczeństwo, brak zależności, CSP | musi | R1 |
| NF-006 | UTC, wstrzykiwalny `since` | musi | R1 |

Poza zakresem (z intent.md i CHG-3/D2): rozróżnienie udane/nieudane, nowy endpoint, wykres/trend, konfigurowalne okno,
autoryzacja widoczności, zmiany zapisu wdrożeń i schematu bazy, włączenie flagi na prod.

## Pytania do bramki
- Właściciel aplikacji sdlc-proba: P-01 — czy przy `?env=` innym niż bieżące środowisko etykieta licznika ma podawać nazwę środowiska (np. „Wdrożenia w ostatnich 7 dniach (prod): N"), czy zostaje dosłowny tekst ze zgłoszenia, a nieznane `?env=` liczy dla środowiska domyślnego (propozycja z FR-003)?
- Właściciel aplikacji sdlc-proba: P-02 — jaki maksymalny czas odpowiedzi `GET /` (z licznikiem) uznajemy za próg porażki, skoro decyzje CHG-3/D2 nie podają liczby (np. p95 poniżej 200 ms przy 10 000 wdrożeń w bazie)?
