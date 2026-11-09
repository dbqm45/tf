# Plan A2: wzorce aplikacji biznesowej w `pack-it`

Stan: 2026-11-09. Plan nadrzędny: `docs/plans/2026-11-09-luki-katalogu-i-autonomia.md` (A2).
Decyzja człowieka 2026-11-09: wariant w `pack-it` zamiast osobnej nakładki `pack-admin` — wzorce występują w każdej
aplikacji biznesowej (CPMS, eMSP, systemy wewnętrzne, panele), a nie tylko w panelach administracyjnych.

## Luka (sprawdzone 2026-11-09 wyszukaniem słów w skillach, przegląd zgrubny)
Soft delete 0, impersonacja 0, tabele danych z filtrowaniem po stronie serwera słabo, command palette 1, audit log
jako funkcja produktu 4, ABAC 1. Podstawy są w `be-auth-security`, `be-api-design`, `be-database`,
`fe-architecture`, `ux-feature-design` — nowe treści ich nie powtarzają, tylko dokładają wzorce i odsyłają.

## A2a — skill `be-business-app-patterns` (nazwa robocza), osobny PR
Scenariusze przed treścią (≥2 trigger, 1 brzegowy, no-trigger z sąsiadami `be-auth-security` i `be-database`),
potem treść:
- **uprawnienia**: role → uprawnienia → zasoby; RBAC, a kiedy ABAC (własność rekordu, dzierżawa, region, stan
  obiektu); sprawdzenie zawsze po stronie serwera, UI tylko ukrywa; test „ten sam request z rolą bez uprawnienia”;
- **audit log**: kto, co, kiedy, skąd, stan przed i po, powód; zapis w tej samej transakcji co zmiana albo przez
  outbox; tylko dopisywanie; retencja; dane osobowe w logu;
- **soft delete**: kiedy tak (przywracanie, relacje, audyt), kiedy nie (RODO art. 17 — usunięcie albo
  anonimizacja); unikalność i indeksy z `deleted_at`; filtr domyślny i jego pułapki;
- **impersonacja** (support działa jako klient): osobne uprawnienie, powód lub zgłoszenie, znacznik w sesji i każdym
  wpisie audytu, baner w UI, zakaz operacji wrażliwych (hasło, płatności, MFA), limit czasu;
- **operacje masowe**: podgląd liczby i próbki, potwierdzenie, zadanie w tle, idempotencja, częściowe błędy
  z raportem, cofnięcie, limit;
- **operacje nieodwracalne**: potwierdzenie przez wpisanie nazwy, drugi czynnik dla krytycznych, okres karencji.
Skill dostają role `backend` i `security-engineer` (`packs/pack-it/roles/`); `frontend` odwołuje się przez
`fe-architecture`.

## A2b — tabele danych i eksport, osobny PR
Rozszerzenia istniejących skilli (nowe scenariusze do ich plików ewaluacji):
- `fe-architecture` — referencja „tabele danych”: stan filtrów i sortowania w URL, wirtualizacja wierszy,
  zaznaczanie „wszystkich pasujących” a operacja masowa, command palette, dostępność tabel (nagłówki, sortowanie
  ogłaszane czytnikowi);
- `be-api-design` — filtrowanie i sortowanie po stronie serwera (lista dozwolonych pól, indeksy), paginacja
  kursorowa, eksport w tle (zadanie → plik → powiadomienie, limit, dane osobowe w pliku).

## A2c — moduł `tf analyze` `authz` w `pack-it`, osobny PR (TDD)
Wzorzec modułu `security` (`packs/pack-it/analyzers/security/`): `analyzer.yaml`, `scripts/scan.py`, fixtures
z trafieniami prawdziwymi i fałszywymi, bramka `min_recall` / `max_false_positives`. Reguły startowe:
- trasa zmieniająca dane (`POST`/`PUT`/`PATCH`/`DELETE`) bez dekoratora lub middleware uprawnień — Express,
  NestJS, Spring, FastAPI, Next.js route handlers;
- uprawnienie sprawdzane tylko w kodzie frontu (warunek na roli w komponencie, brak odpowiednika na serwerze —
  heurystyka, niska waga);
- `DELETE`/`UPDATE` w handlerze bez wywołania audytu (heurystyka, niska waga, tylko gdy projekt ma audit log).

## Kolejność
A2a → A2b → A2c; każdy krok to osobny PR z bramką (`skill_gate.py`, `sync-gate`, `workspace.py check --packs
pack-it` i `--packs all`, `refs`), płatna ewaluacja za zgodą człowieka.
