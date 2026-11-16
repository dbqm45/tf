---
artifact: adr
phase: architecture
status: accepted
version: 1
author: tomasz-solution-architect
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md, docs/project/04-architecture/stack-decision.md]
---
# 0002. Spójność rezerwacji: PostgreSQL + exclusion constraint na (zasób, przedział)

## Kontekst
Scenariusz (H,H): 50 osób jednocześnie rezerwuje tę samą salę o 9:00 → dokładnie 1 sukces, reszta czytelna odmowa,
0 podwójnych rezerwacji. Sale rezerwuje się na dowolny przedział (H1), biurka na dzień (H2), facility blokuje zasób do
serwisu (H3), system zwalnia rezerwacje no-show (H4). Każdy z tych przypadków zajmuje zasób w czasie (archetyp Availability).

## Decyzja
Azure Database for PostgreSQL Flexible Server 18. Jedna tabela alokacji (rezerwacje **i** blokady serwisowe) z kolumną
`period tstzrange` (granice `[)`, więc sąsiednie przedziały się nie kolidują) i ograniczeniem:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- wcześniej dodać do parametru azure.extensions
ALTER TABLE allocation ADD CONSTRAINT allocation_no_overlap
  EXCLUDE USING gist (resource_id WITH =, period WITH &&)
  WHERE (status IN ('BOOKED', 'CHECKED_IN', 'BLOCKED'));
```

Aplikacja robi wstępne sprawdzenie dostępności (dla ładnego komunikatu), ale **gwarancją jest ograniczenie w bazie**:
błąd SQLSTATE `23P01` mapujemy na wynik operacji „odrzucono: zasób zajęty” (HTTP 409, kod `RESOURCE_UNAVAILABLE`).
Zwolnienie (anulowanie, no-show) = zmiana statusu poza predykat `WHERE`, więc przedział od razu wraca do puli.
No-show: zadanie co minutę wykonuje jeden idempotentny `UPDATE … SET status = 'RELEASED' … RETURNING id` — bezpieczny także przy kilku instancjach.

## Rozważane opcje
- Exclusion constraint (wybrana) — zalety: gwarancja niezależna od ścieżki kodu (także przyszłe importy, zadania, nowe typy zasobów), dowolne przedziały, blokady serwisowe w tym samym mechanizmie; wady: specyficzne dla PostgreSQL, wymaga `btree_gist`, JPA nie wyraża typu zakresu wprost (mapowanie przez natywny typ / Hibernate custom type — spike S1).
- `SELECT … FOR UPDATE` na wierszu zasobu + sprawdzenie nakładania + insert — zalety: przenośne, proste; wady: poprawność zależy od tego, czy **każda** ścieżka zapisu pobierze blokadę; serializuje wszystkie rezerwacje zasobu. Opcja zapasowa, jeśli S1 wypadnie źle.
- Optimistic locking (`@Version` na zasobie/dniu) — wady: przy 50 równoczesnych próbach 49 konfliktów i ponowień, więcej kodu obsługi.
- Unikalny indeks na (zasób, slot) przy stałej siatce slotów (np. 15 min) — zalety: najprostszy mechanizm bazy; wady: wiele wierszy na rezerwację, sztywna granulacja, blokady serwisowe wielodniowe = setki wierszy.
- `SERIALIZABLE` dla transakcji rezerwacji — poprawne, ale błędy serializacji i ponowienia przy szczycie; brak przewagi nad ograniczeniem.

## Konsekwencje
- Punkt wrażliwości spójności leży w schemacie bazy — zmiany migracji `allocation` wymagają przeglądu.
- Fitness function w CI: test Testcontainers (PostgreSQL 18) z 50 równoległymi żądaniami → dokładnie 1 sukces.
- Uzależnienie od PostgreSQL (akceptowane; Azure Flexible Server jest usługą zarządzaną).
- Biurko na dzień = przedział [00:00, 24:00) w strefie biura — potrzebna jawna decyzja o strefie czasowej (przechowujemy `timestamptz`, UTC).
