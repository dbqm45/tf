<!-- WYGENEROWANO przez .claude/hooks/project_record.py — nie edytuj ręcznie -->
# Dziennik projektu

**Bieżąca faza:** Plan  ·  **Do akceptacji:** 1  ·  [Dziennik zdarzeń](journal.md)  ·  [Rejestr decyzji](decisions.md)

| Faza | Artefakt | Status | Wersja | Autor | Aktualizacja | TL;DR |
|---|---|---|---|---|---|---|
| Odkrywanie | [Brief: Rezerwacja sal i biurek](01-discovery/brief.md) | accepted | 1 | użytkownik | 2026-09-27 | Firma (300 osób, model hybrydowy) rezerwuje sale i biurka w arkuszu — dochodzi do podwójnych rezerwacji. Cel: aplikacja webowa |
| Wymagania | [Wymagania: Rezerwacja sal i biurek](03-requirements/requirements.md) | accepted | 1 | użytkownik | 2026-09-27 | 6 historyjek MVP. Kluczowe atrybuty: brak podwójnych rezerwacji przy współbieżności, SSO M365, dostępność w godzinach pracy 99,5%. |
| Architektura i stack | [0001. Styl architektury: modularny monolit (Spring Modulith)](04-architecture/adr/0001-modularny-monolit.md) | accepted | 1 | tomasz-solution-architect | 2026-09-27 |  |
| Architektura i stack | [0002. Spójność rezerwacji: PostgreSQL + exclusion constraint na (zasób, przedział)](04-architecture/adr/0002-spojnosc-rezerwacji-postgresql-exclusion-constraint.md) | accepted | 1 | tomasz-solution-architect | 2026-09-27 |  |
| Architektura i stack | [0003. Hosting: App Service (Linux) + PostgreSQL Flexible Server w jednym regionie UE](04-architecture/adr/0003-hosting-app-service-region-ue.md) | accepted | 1 | tomasz-solution-architect | 2026-09-27 |  |
| Architektura i stack | [0004. Integracja z M365: Microsoft Graph, uprawnienia aplikacyjne, outbox, synchronizacja w jedną stronę](04-architecture/adr/0004-integracja-m365-graph-outbox.md) | accepted | 1 | tomasz-solution-architect | 2026-09-27 |  |
| Architektura i stack | [Decyzja o stacku: Rezerwacja sal i biurek (MVP)](04-architecture/stack-decision.md) | accepted | 1 | tomasz-solution-architect | 2026-09-27 | Modularny monolit: **Java 25 + Spring Boot 4.1 + Spring Modulith 2.x** (backend) i **Angular 22 + MSAL Angular** (front, serwowany z tej sam… |
| Plan | [Plan realizacji: Rezerwacja sal i biurek (MVP)](05-plan/plan.md) | proposed | 1 | jan | 2026-09-27 | 8 kroków (cięć pionowych), każdy wdrażalny. Krok #1 (szkielet + CI) zaraz po akceptacji tego planu. |

## Ostatnie przekazanie — z [05-plan/plan.md](05-plan/plan.md)

- **Dla:** jan-backend (krok #1), równolegle jan-ddd-analyst (krok #2a, może zacząć od razu, niezależnie od #1)
- **Zadanie:** krok #1 — szkielet modułów Spring Modulith + CI z `ApplicationModules.verify()`; krok #2a — tactical design agregatu `Allocation`
- **Przeczytaj:** TL;DR, wiersze kroków #1 i #2a, ADR-0001, ADR-0002
- **Nie rób:** nie zaczynaj kroku 8 (M365) przed odpowiedzią IT; nie buduj kroku 3 przed #2a (ryzyko modelu bez ustalonych niezmienników)
- **Gotowe, gdy:** krok #1 wdrożony i zielony w CI, krok #2a ma zapisany model w `02-domain/`, oba zaakceptowane przez użytkownika

## Ostatnie zdarzenia

| Kiedy | Kto | Faza | Zdarzenie |
|---|---|---|---|
| 2026-09-27 08:09 | system | meta | Utworzono dziennik projektu (docs/project/) |
| 2026-09-27 08:15 | tomasz | architecture | Rekomendacja stacku (proposed): modularny monolit Java 25/Spring Boot 4.1 + Angular 22 + PostgreSQL 18 na App Service w regionie UE; ADR-0001..0004, D-001..D-005; czeka na akceptację użytkownika i odpowiedzi IT (04-architecture/stack-decision.md) |
| 2026-09-27 08:16 | użytkownik | architecture | Zaakceptowano stack-decision v1 i ADR-0001..0004; IT potwierdza: sale nie są skrzynkami Exchange, zgoda admina M365 będzie |
| 2026-09-27 08:18 | jan | plan | Plan realizacji (proposed): 8 kroków, walking skeleton -> H6 -> tactical design agregatu Allocation -> H1 (bez M365) -> H5/H2/H3/H4 -> integracja M365 (blokowana odpowiedzią IT); 05-plan/plan.md |
