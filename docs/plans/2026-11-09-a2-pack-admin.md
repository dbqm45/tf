# Plan A2: nakładka `pack-admin` — pierwszy profil aplikacji (panel administracyjny)

Stan: 2026-11-09, do akceptacji. Plan nadrzędny: `docs/plans/2026-11-09-luki-katalogu-i-autonomia.md` (A2).
Przewodnik: `docs/new-pack.md`; publiczne API nakładki: `core/factory/PUBLIC_API.md`.

## Luka (sprawdzone 2026-11-09 wyszukaniem słów w skillach, przegląd zgrubny)
Soft delete 0, impersonacja 0, tabele danych z filtrowaniem po stronie serwera słabo, command palette 1, audit log
jako funkcja produktu 4, ABAC 1. Ogólne podstawy są w `pack-it` (`be-auth-security`, `be-api-design`,
`be-database`, `fe-architecture`) i `pack-ux` (`ux-feature-design`, `ux-accessibility`) — nakładka ich nie
powtarza, tylko dokłada wzorce typowe dla paneli i odsyła do podstaw.

## Zakres nakładki
Pytania, które obsługuje: „jak zaprojektować uprawnienia w panelu”, „audit log — co zapisywać”, „usuwać czy
oznaczać jako usunięte”, „logowanie jako klient przez support”, „operacja masowa na 10 tys. rekordów”, „tabela
z filtrami, sortowaniem i eksportem dużych danych”, „czy endpointy admina są zabezpieczone”.
Poza zakresem (sąsiedzi): ogólne uwierzytelnianie i sesje (`be-auth-security`), projekt API (`be-api-design`),
schemat i migracje (`be-database`), UX funkcji i stany ekranów (`ux-feature-design`), dostępność ogólnie
(`ux-accessibility`), wielodzierżawność (`arch-multi-tenancy`).

## Elementy i kolejność (osobne PR)
1. **A2a — szkielet** (`tools/workspace.py new-pack admin --prefix admin-`): `pack.yaml` (`0.1.0`,
   `default: false`, `requires.packs: [pack-it]`, `optional_packs: [pack-ux]`), wymiar `admin-`, wpis w macierzy
   CI. Bez treści — szkielet scenariuszy celowo nie przechodzi bramki, więc A2a łączę z A2b w jednym PR.
2. **A2b — skill `admin-patterns`**: scenariusze przed treścią (≥2 trigger, 1 no-trigger z sąsiadem
   `be-auth-security`, 1 brzegowy), potem treść:
   - model uprawnień: role → uprawnienia → zasoby; RBAC, a kiedy ABAC (własność rekordu, dzierżawa, region);
     sprawdzanie zawsze po stronie serwera, UI tylko ukrywa;
   - audit log: kto, co, kiedy, skąd, stan przed i po, powód; zapis w tej samej transakcji co zmiana albo przez
     outbox; tylko dopisywanie; retencja i dane osobowe w logu;
   - soft delete: kiedy tak (przywracanie, relacje, audyt), kiedy nie (RODO art. 17 — usunięcie albo
     anonimizacja), indeksy i unikalność z `deleted_at`, filtr domyślny;
   - impersonacja: uprawnienie, zgoda lub zgłoszenie, znacznik w sesji i w każdym wpisie audytu, baner w UI,
     zakaz operacji wrażliwych (hasło, płatności, MFA), limit czasu;
   - operacje masowe: podgląd liczby i próbki, potwierdzenie, zadanie w tle, idempotencja, częściowe błędy
     z raportem, cofnięcie, limit;
   - potwierdzenia operacji nieodwracalnych (wpisanie nazwy, drugi czynnik dla krytycznych).
3. **A2c — skill `admin-data-tables`** (gdy `admin-patterns` przekroczy rozsądny rozmiar albo ewaluacja pokaże
   potrzebę): paginacja kursorowa a offsetowa, filtrowanie i sortowanie po stronie serwera z indeksami, stan
   w URL, wirtualizacja wierszy, eksport w tle (zadanie → plik → powiadomienie, limit, dane osobowe), operacje
   masowe z zaznaczania „wszystkich pasujących”, dostępność tabel, command palette.
4. **A2d — moduł `tf analyze` `admin-authz`** (tier 0, TDD): wzorzec modułu `security`. Reguły startowe:
   trasy z prefiksem admina bez dekoratora lub middleware uprawnień (Express, NestJS, Spring, FastAPI, Next.js
   route handlers); operacje `DELETE`/`UPDATE` w handlerach admina bez wywołania audytu (heurystyka, niska waga);
   sprawdzenie roli tylko w kodzie frontu. Fixtures z trafieniami prawdziwymi i fałszywymi, bramka
   `min_recall` / `max_false_positives`.
5. **Role i persona**: `contributes` dokłada `admin-patterns` rolom backend i frontend z `pack-it` (bez nowej
   persony); konsultant `admin-consult` (tylko odpowiedź) dla pytań o panel.

## Decyzje do potwierdzenia
- **D1 — prefiks `admin-`** (rekomendacja) czy ogólniejszy `app-` pod przyszłe profile (SaaS, e-commerce)?
  Rekomendacja: `admin-`; każdy profil dostaje własną nakładkę i prefiks.
- **D2 — `requires: pack-it`** (rekomendacja: tak — bez backendu i frontu skille nie mają podstaw) i `pack-ux`
  jako opcjonalna.
- **D3 — bez nowej persony** (rekomendacja), skille dokładane istniejącym rolom; persona dopiero, gdy pojawi się
  potrzeba prowadzenia całego panelu jedną osobą.
- **D4 — A2c od razu czy po ewaluacji A2b?** Rekomendacja: po ewaluacji.

## Sprawdzenie
`skill_gate.py <skill>` i `--hints` w `.work/h-all`, `sync-gate`, `workspace.py check --packs pack-admin` i
`--packs all`, `refs`; testy modułu (`packs/pack-admin/tests/`); płatna ewaluacja za zgodą człowieka.
