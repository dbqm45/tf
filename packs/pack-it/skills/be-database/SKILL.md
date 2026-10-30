---
name: be-database
description: Użyj przy relacyjnej bazie — schemat, migracje, indeksy, zapytania SQL/ORM, transakcje, N+1, wydajność i skalowanie.
metadata:
  przeglad: "2027-10-17"
  katalog: "Użyj przy pracy z relacyjną bazą danych — schemat, migracje, indeksy, zapytania SQL/ORM, transakcje, wydajność zapytań (N+1), wzorce PoEAA (Unit of Work, Identity Map, Data Mapper). Nie do projektowania endpointów (be-api-design) ani infrastruktury bazy (ops-iac-terraform)."
  slowa: "blokada optymistyczna, blokada pesymistyczna, blokady w PostgreSQL, wyścig o ostatnie miejsce, dwóch użytkowników kupuje to samo, nadpisują sobie edycję, SELECT FOR UPDATE, wersja wiersza, zakleszczenie, write skew"
---

# Baza danych

## Migracje — bezpieczne na produkcji
1. Każda zmiana schematu = migracja w repo. Nigdy ręczne zmiany na bazie.
2. Migracje są **wstecznie kompatybilne** z poprzednią wersją aplikacji (deploy i rollback bez przestoju).
3. Zmiany niekompatybilne przez expand → migrate → contract (backfill w partiach, usunięcie starej kolumny w osobnym
   wydaniu); indeksy na dużych tabelach `CONCURRENTLY`, `NOT NULL` na dużej tabeli nie w jednym kroku.
4. Każda migracja ma sensowny `down` albo jest jawnie oznaczona jako nieodwracalna.

## Zapytania
- Zawsze parametryzowane. Konkatenacja stringów w SQL = błąd krytyczny.
- Wybieraj potrzebne kolumny, nie `SELECT *` w kodzie produkcyjnym.
- Wykrywaj N+1: pętla z zapytaniem w środku → join / `IN (...)` / eager loading.
- Wzorce logiki i dostępu do danych (skrypt transakcji vs model domeny, Active Record vs Data Mapper, Unit of Work,
  Identity Map, lazy loading, ORM do zapisu i SQL do odczytu, DTO i mappery): `references/wzorce-dostepu-do-danych.md`.
- Każde zapytanie po kolumnie w `WHERE`/`JOIN`/`ORDER BY` na dużej tabeli ma indeks — sprawdź `EXPLAIN ANALYZE`.
- Wydajność w produkcji (pula połączeń i jej rozmiar, wolne zapytania i `pg_stat_statements`, VACUUM, repliki,
  widoki zmaterializowane, partycjonowanie, sharding): `references/wydajnosc-bazy.md`.

## Transakcje
- Operacje, które muszą się udać razem, w jednej transakcji; transakcje krótkie, bez wywołań sieciowych w środku.
- Wyścigi — wybór blokady, po kolei:
  1. czy jedno atomowe zapytanie (`UPDATE … SET wolne = wolne - 1 WHERE id = … AND wolne >= 1`, sprawdzona liczba
     zmienionych wierszy) albo ograniczenie (`UNIQUE`, `EXCLUDE`) usuwa okno między odczytem a zapisem — wtedy bez blokady;
  2. okno dłuższe niż jedna krótka transakcja (formularz, kilka żądań) → wersja wiersza / `ETag` + `If-Match`
     (optymistycznie) albo dzierżawa z wygaśnięciem w aplikacji; nigdy transakcja otwarta na czas myślenia użytkownika;
  3. rzadkie trafienia w ten sam wiersz → optymistycznie, z ograniczoną liczbą ponowień i jitterem; gorący wiersz →
     `SELECT … FOR UPDATE` (pesymistycznie);
  4. utracona praca kosztowna (skutek zewnętrzny, nieidempotentny) → blokada przed pracą.
  Pułapki: zakleszczenia (stała kolejność blokowania), żadnych wywołań sieciowych pod blokadą wiersza, `NOWAIT` albo
  limit czasu oczekiwania zamiast wiszenia; wersja wiersza nie chroni przed *write skew* (reguła na kilku wierszach —
  izolacja Serializable albo blokada wspólnego rodzica); blokada w Redis tylko dla wydajności, dla poprawności tokeny
  ogrodzeniowe (fencing tokens).
- Masowy zapis z wersją (`UPDATE … FROM (VALUES …) WHERE version = …`): sprawdź, że liczba zmienionych wierszy = oczekiwanej;
  mniej → konflikt, wycofaj całość.
- **Outbox:** tabela (id nadane przy zapisie, typ, ładunek, status, czas utworzenia; indeks po statusie i czasie) zapisywana w tej
  samej transakcji co stan; sprzątanie wysłanych; wielu pobierających → `FOR UPDATE SKIP LOCKED` lub compare-and-set statusu.
- **Inbox (deduplikacja):** `UNIQUE(message_id)` + `INSERT … ON CONFLICT DO NOTHING` w tej samej transakcji co efekt — nie
  „sprawdź, potem zapisz”. Szczegóły: be-messaging-outbox.

## Read modele
Łączenie ciągłych okresów i agregaty po przedziałach rób funkcjami okna (`LAG`, `SUM() OVER`) w SQL — zamiast pętli w aplikacji.
Dla przedziałów czasu: typy zakresów + ograniczenie wykluczające (PostgreSQL), gdy baza je ma (ddd-archetypes → availability).
Schemat per moduł (np. osobny `schema` w PostgreSQL) wzmacnia granice modułów w monolicie.

## Integralność
- Klucze obce, `UNIQUE`, `CHECK` w bazie — nie tylko walidacja w aplikacji.
- Czas w UTC (`timestamptz`), pieniądze jako `numeric`/liczby całkowite w groszach, nigdy `float`.

## Checklista
- [ ] migracja kompatybilna wstecz i przetestowana (up + down)
- [ ] brak N+1, indeksy dla nowych zapytań
- [ ] brak surowego SQL z konkatenacją
