---
name: arch-multi-tenancy
description: Użyj przy SaaS dla wielu klientów — model izolacji najemców, kontekst najemcy w żądaniu i kolejce, RLS, hałaśliwy sąsiad, migracje, testy izolacji.
metadata:
  widocznosc: nazwa
  przeglad: 2027-10-20
  katalog: "Użyj, gdy projektujesz lub przeglądasz SaaS obsługujący wielu klientów (najemców, tenantów) — wybór modelu izolacji (silos, pula, model mieszany) z kryteriami, kontekst najemcy w żądaniu HTTP, kolejce, zadaniu w tle, cache i logach, izolacja w bazie (kolumna najemcy z RLS w PostgreSQL, schemat lub baza na najemcę), hałaśliwy sąsiad (limity, kwoty, koszt per najemca), migracje na wielu najemcach, testy izolacji jako stała część regresji, eksport i usunięcie danych klienta, wejście i odejście najemcy. Nie do ogólnego schematu i indeksów (be-database), logowania i ról użytkowników (be-auth-security), RODO (arch-privacy-compliance), mapy przepisów (arch-eu-product-law) ani izolacji najemców w systemach AI (arch-ai-solutions)."
  slowa: "multi-tenancy, multi-tenant, wielodzierżawność, najemca, tenant, tenant_id, izolacja klientów, izolacja danych klientów, firma A widzi dane firmy B, wyciek między klientami, silo, pool, bridge, baza na klienta, schemat na klienta, row level security, RLS, polityka wierszy, kontekst najemcy, kontekst tenanta w kolejce, zadanie w tle innego klienta, noisy neighbor, hałaśliwy sąsiad, limity na klienta, kwoty, koszt per klient, migracja wielu baz klientów, onboarding klienta SaaS, offboarding, usunięcie danych klienta, eksport danych klienta"
---

# Wielodzierżawność (multi-tenancy) w SaaS

**Rola agenta:** dobiera model izolacji najemców do wymagań i pilnuje, żeby kontekst najemcy był jawny na każdej
ścieżce: żądanie, kolejka, zadanie w tle, cache, logi, eksport. Wyciek danych między klientami to incydent
bezpieczeństwa i naruszenie RODO, więc izolację udowadnia test, a nie przegląd kodu.

## 1. Model izolacji — wybór
| Model | Co dzielą najemcy | Mocna strona | Koszt | Rozsądny, gdy |
|---|---|---|---|---|
| **pula** (pool) | aplikację i bazę; wiersze z kolumną najemcy | najtańszy, jedna migracja, łatwe wejście klienta | izolacja zależy od każdego zapytania; hałaśliwy sąsiad | wielu małych klientów, brak wymogów umownych |
| **schemat na najemcę** | aplikację i serwer bazy | izolacja przez `search_path`/uprawnienia, łatwy eksport | migracje × liczba schematów; limit setek–tysięcy | dziesiątki–setki średnich klientów |
| **silos** (silo) | nic albo tylko płaszczyznę zarządzania | pełna izolacja, osobne SLA, rezydencja danych | koszt infrastruktury i operacji × N | klienci regulowani, umowa wymaga osobnej bazy |
| **mieszany** (bridge, poziomy) | pula dla planu podstawowego, silos dla Enterprise | cena pasuje do planu | dwie ścieżki wdrożenia i testów | różne plany o różnych wymaganiach |

Kryteria: liczba i wielkość klientów, wymogi umów i regulacji (osobna baza, region), koszt na klienta, rozrzut
obciążenia, szybkość wejścia nowego klienta, zespół do utrzymania. Domyślnie: **pula z RLS**, silos tylko tam, gdzie
wymaga go umowa lub ryzyko. Decyzję zapisujesz jako ADR (docs-tech-writing) z kryterium rewizji (np. „klient > 20% ruchu”).
Płaszczyzna zarządzania (rejestr najemców, plany, wejście i odejście klienta, metryki per najemca) jest wspólna
dla wszystkich modeli.

## 2. Kontekst najemcy — jawny na każdej ścieżce
- **Żądanie:** najemcę ustala serwer z uwierzytelnionej tożsamości (claim w tokenie, członkostwo w organizacji),
  nigdy z parametru lub nagłówka podanego przez klienta bez sprawdzenia członkostwa (be-auth-security).
- **Kolejka i zadanie w tle:** identyfikator najemcy w ładunku albo nagłówku każdej wiadomości; konsument ustawia
  kontekst przed pierwszym zapytaniem i czyści go po zadaniu. Zadanie bez najemcy kończy się błędem, nie domyślnym
  kontekstem. Zadania „dla wszystkich” iterują po rejestrze najemców, po jednym kontekście naraz.
- **Cache, pliki, wyszukiwarka:** klucz cache i ścieżka w magazynie obiektów zaczynają się od najemcy; indeks
  wyszukiwania filtruje po najemcy po stronie serwera.
- **Logi i metryki:** najemca w każdym wpisie (ops-observability) — bez tego nie policzysz kosztu ani zakresu incydentu.
- Kontekst w zmiennej wątku lub asynchronicznej (`AsyncLocalStorage`, `contextvars`, `ThreadLocal`) przekazujesz
  świadomie przy przejściu do innego wątku lub puli; pula wątków bez czyszczenia przenosi najemcę do następnego zadania.

## 3. Izolacja w bazie
- **Pula w PostgreSQL:** kolumna najemcy w każdej tabeli z danymi klienta (także w kluczach obcych i indeksach
  złożonych, najemca na początku), RLS z polityką porównującą kolumnę z ustawieniem transakcji
  (`set_config('app.tenant_id', …, true)` lub `SET LOCAL`). Szczegóły i pułapki: `references/rls-postgresql.md`.
- Aplikacja łączy się rolą bez uprawnień właściciela tabel i bez omijania RLS; migracje działają osobną rolą.
- Pula połączeń w trybie transakcyjnym: ustawienie najemcy tylko na czas transakcji, nigdy na sesję.
- Druga linia obrony: repozytorium lub ORM dokłada filtr najemcy — RLS łapie to, czego filtr nie dołożył.
- Tabele globalne (słowniki, plany) oznaczasz jawnie; reszta jest domyślnie per najemca.

## 4. Hałaśliwy sąsiad i koszt
- Limity per najemca: żądania na sekundę, równoległe zadania, rozmiar importu, miejsce na pliki (be-api-design: 429).
- Kolejki: sprawiedliwy przydział (osobna kolejka lub limit współbieżności na najemcę) zamiast jednej FIFO.
- Koszt per najemca z metryk i tagów (ops-finops) — pokazuje, kiedy klient powinien przejść do silosu albo innego planu.

## 5. Migracje i cykl życia najemcy
- Pula: jedna migracja, ale wykonywana na dużej tabeli — wzorzec rozszerz i zawęź (be-database).
- Schemat lub silos: migracja w falach (najpierw najemcy wewnętrzni), status migracji per najemca, wznowienie
  od miejsca błędu; aplikacja działa ze starą i nową wersją schematu w trakcie fal.
- **Wejście:** rejestr najemców, utworzenie zasobów automatem (ops-iac-terraform dla silosu), dane startowe.
- **Odejście i prawa klienta:** pełny eksport danych najemcy w formacie ustrukturyzowanym (Data Act —
  arch-eu-product-law), usunięcie z kopiami zapasowymi wg retencji (arch-privacy-compliance), dowód usunięcia.

## 6. Testy izolacji — stała część regresji
- Dwóch najemców w danych testowych każdego testu integracyjnego; dla każdego zasobu API: zalogowany w A, żądanie
  o identyfikator z B → 404 (nie 403, żeby nie zdradzać istnienia).
- Test RLS bezpośrednio w bazie: rola aplikacji bez ustawionego najemcy widzi zero wierszy.
- Test kolejki: wiadomość najemcy A obsłużona po wiadomości B nie widzi danych B.
- Test cache i eksportu: klucze i pliki nie krzyżują się.
- Testy w zestawie regresji (qa-regression) i w CI przy każdej zmianie; nowa tabela bez polityki RLS = czerwony test
  (zapytanie do katalogu: tabele z kolumną najemcy bez włączonego RLS).

## Zasady
- Kontekst najemcy jawny i sprawdzony po stronie serwera na każdej ścieżce; brak kontekstu = błąd, nie „wszyscy”.
- Izolację udowadnia test z dwoma najemcami, nie przegląd kodu.
- Panel administracyjny „widzi wszystkich” tylko przez osobną rolę z audytem dostępu (be-auth-security).
- Wyciek między najemcami traktujesz jak incydent (ops-security-operations) i naruszenie danych (arch-privacy-compliance).

## Przykład
**Sytuacja:** „SaaS B2B, PostgreSQL, 300 klientów w jednej bazie, kolumna `tenant_id`. Raport z kolejki pokazał dane
innego klienta.”
**Wynik (skrót):**
- Model: pula zostaje (300 podobnych klientów, brak wymogów umownych); ADR z kryterium rewizji dla klientów Enterprise.
- Przyczyna: worker czytał najemcę z ustawienia sesji połączenia z puli — poprzednie zadanie zostawiło inny `tenant_id`.
- Poprawka: najemca w ładunku wiadomości; worker ustawia go `SET LOCAL` w transakcji zadania; RLS z polityką na
  `current_setting('app.tenant_id')`, rola aplikacji bez omijania RLS.
- Testy: zadanie A po zadaniu B na tym samym połączeniu; rola aplikacji bez najemcy widzi 0 wierszy; test katalogu
  „każda tabela z `tenant_id` ma RLS”.
- Zgłoszenie incydentu i ocena naruszenia → ops-security-operations, arch-privacy-compliance.

## Checklista
- [ ] model izolacji wybrany wg kryteriów, ADR z kryterium rewizji
- [ ] najemca z uwierzytelnionej tożsamości; obecny w żądaniu, wiadomości, zadaniu, cache, plikach, logach
- [ ] RLS (albo osobny schemat lub baza) i rola aplikacji bez omijania polityk; ustawienie najemcy na transakcję
- [ ] limity i koszt per najemca
- [ ] migracje dla wszystkich najemców z wznowieniem; eksport i usunięcie danych klienta
- [ ] testy izolacji z dwoma najemcami w regresji i CI

## Źródła
Opisane własnymi słowami; fakty i daty dostępu w `references/rls-postgresql.md`.
