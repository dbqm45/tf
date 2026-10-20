---
artifact: plan
phase: plan
status: proposed
version: 1
author: jan
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/04-architecture/stack-decision.md, docs/project/04-architecture/adr/0001-modularny-monolit.md, docs/project/04-architecture/adr/0002-spojnosc-rezerwacji-postgresql-exclusion-constraint.md, docs/project/04-architecture/adr/0004-integracja-m365-graph-outbox.md, docs/project/03-requirements/requirements.md]
---
# Plan realizacji: Rezerwacja sal i biurek (MVP)

## TL;DR
8 kroków (cięć pionowych), każdy wdrażalny. Krok #1 (szkielet + CI) zaraz po akceptacji tego planu.
Pierwsze cięcie z wartością biznesową: #2 (H6 SSO) → #3 (H1 rezerwacja sali, bez M365). Integracja M365 (#8) jest
odsunięta na koniec i zależy od odpowiedzi IT (S2/S3) — bez niej H1 działa, tylko bez wpisu w kalendarzu M365.
Wąskie gardło: 1 programista Java na cały moduł `booking`/`resources`/`identity` — kroki backendowe idą sekwencyjnie.

## Kroki (cięcia pionowe, każdy wdrażalny)
| # | Krok | Historyjki | Wykonawca (persona/rola, tier) | Kryteria „gotowe” | Zależy od |
|---|---|---|---|---|---|
| 1 | Szkielet: moduły Spring Modulith (`identity`, `resources`, `booking`, `calendarsync` jako puste porty), `ApplicationModules.verify()` w CI, Testcontainers, workspace Angular + routing pusty, pipeline (GitHub Actions — do potwierdzenia z IT), wdrożenie pustej apki na App Service dev. Obejmuje spike S0 (dostępność usług w regionie) i S4 (MSAL Angular 22). | — (walking skeleton) | jan-backend (std) + zespół frontend Angular (poza zespołem jan) | Pipeline zielony; `verify()` bez naruszeń; apka wdraża się i odpowiada na `/actuator/health` w regionie docelowym | ADR-0001..0003 zaakceptowane (są) |
| 2 | Logowanie SSO Entra ID, moduł `identity` | H6 | jan-backend (std, skille be-auth-security) + frontend (MSAL Angular) | Pracownik loguje się kontem firmowym; backend weryfikuje token (resource server), role dostępne w kontekście żądania | Krok 1 |
| 2a | Tactical design agregatu rezerwacji: `Allocation`/`Booking` (archetyp Availability), niezmienniki, obiekty wartości (przedział, status), granica spójności — przed implementacją kroku 3 | — | jan-ddd-analyst (deep, ddd-tactical-design + ddd-archetypes) | Krótki model zapisany w `02-domain/` (agregat, invarianty, mapowanie na `allocation` z ADR-0002) | Krok 1 |
| 3 | Rezerwacja sali na przedział czasu, **bez** synchronizacji M365 (moduły `booking`+`resources`) — obejmuje spike S1 (exclusion constraint + JPA + test 50 równoległych) | H1 (częściowo — bez wpisu w M365) | jan-backend (std) | Fitness function z ADR-0002 przechodzi (50 równoległych → 1 sukces, 49 × `RESOURCE_UNAVAILABLE`); UI rezerwacji sali działa | Krok 2, 2a |
| 4 | Kalendarz dostępności zasobów (widok dnia/tygodnia), model do odczytu na `allocation` | H5 | jan-backend + frontend | Pracownik widzi dostępność sal na dzień/tydzień | Krok 3 |
| 5 | Rezerwacja biurka na dzień — rozszerzenie `resources` o typ zasobu „biurko” (dane + polityka), bez zmian w `booking` | H2 | jan-backend | Test modyfikowalności z ADR-0001 (nowy typ zasobu wyłącznie danymi/konfiguracją) przechodzi; rezerwacja biurka = przedział [00:00,24:00) w strefie biura | Krok 3 |
| 6 | Blokada zasobu do serwisu (rola facility) | H3 | jan-backend | Zablokowany zasób ma status `BLOCKED` w `allocation`, niedostępny do rezerwacji przez fitness function z kroku 3 | Krok 3 |
| 7 | Automatyczne zwolnienie rezerwacji bez potwierdzenia obecności po 15 min | H4 | jan-backend | Zadanie w tle wykonuje idempotentny `UPDATE … RETURNING`; bezpieczne przy >1 instancji App Service | Krok 3 |
| 8 | Integracja M365: moduł `calendarsync`, outbox (Event Publication Registry), Microsoft Graph, uprawnienia aplikacyjne — dopełnia H1 („wpis w M365”) | H1 (dopełnienie) | jan-backend | Rezerwacja sali tworzy/aktualizuje/anuluje wydarzenie w kalendarzu M365; awaria Graph nie blokuje rezerwacji (widoczny stan synchronizacji w UI) | Krok 3; **odpowiedzi IT** (S2, S3) |

## Spike'i
| ID | Pytanie | Kiedy (krok) | Kryterium porzucenia wyboru |
|---|---|---|---|
| S0 | App Service Linux / PostgreSQL Flexible GP dostępne w regionie docelowym? | Krok 1 | Brak usługi → region zapasowy UE (ADR-0003) |
| S1 | Exclusion constraint + JPA: mapowanie `23P01`, zachowanie przy 50 równoległych | Krok 3 | >1 sukces lub p95 > 1 s → wariant `FOR UPDATE` (ADR-0002 opcja B) |
| S2 | Sale już są skrzynkami zasobów Exchange? Dwa źródła prawdy? | Przed krokiem 8 | Nie da się zablokować rezerwacji bezpośrednio w Exchange → nowa wersja ADR-0004, decyzja użytkownika |
| S3 | Zgoda administratora M365 na `Calendars.ReadWrite` (RBAC for Applications) | Przed krokiem 8 | Brak zgody → opcja C ADR-0004 (zaproszenie .ics) |
| S4 | Zgodność MSAL Angular 6.x z Angular 22 | Krok 1 | Błędy runtime/build → BFF (Spring `oauth2Login`, sesja) |

## Ryzyka harmonogramu
- **Bus factor:** 1 programista Java obsługuje kroki 2, 2a→3, 5–8 sekwencyjnie — to oś krytyczna 3-miesięcznego MVP; front-end (2 os. TS/Angular) czeka na kontrakty API z kroków 2–3. Mitigacja: kroki 4–7 mają niezależne fragmenty frontu, które front może budować na mocku API, gdy kontrakt (OpenAPI) z kroku 3 jest ustalony wcześniej.
- **Krok 8 blokowany przez IT** (S2, S3) — jeśli odpowiedzi się opóźnią, MVP dostarczamy bez synchronizacji M365 (H1 częściowo spełnione) i domykamy krok 8 po odpowiedzi, zgodnie z ADR-0004.
- **Region Azure (S0)** nieznany do potwierdzenia — może przesunąć krok 1 o dni, jeśli trzeba zmienić region.

## Otwarte pytania
- [ ] Wszystkie pytania ze `stack-decision.md` pozostają otwarte (źródło prawdy dla sal, zgoda M365, region, potwierdzanie obecności, budżet, repo/CI, kompetencje TS w backendzie) — krok 8 nie startuje bez odpowiedzi na pierwsze dwa.
- [ ] Kto potwierdza „gotowe” po każdym kroku (Product Owner / właściciel produktu) i w jakim rytmie (Sprint Review co ile)? → użytkownik

## Przekazanie
- **Dla:** jan-backend (krok #1), równolegle jan-ddd-analyst (krok #2a, może zacząć od razu, niezależnie od #1)
- **Zadanie:** krok #1 — szkielet modułów Spring Modulith + CI z `ApplicationModules.verify()`; krok #2a — tactical design agregatu `Allocation`
- **Przeczytaj:** TL;DR, wiersze kroków #1 i #2a, ADR-0001, ADR-0002
- **Nie rób:** nie zaczynaj kroku 8 (M365) przed odpowiedzią IT; nie buduj kroku 3 przed #2a (ryzyko modelu bez ustalonych niezmienników)
- **Gotowe, gdy:** krok #1 wdrożony i zielony w CI, krok #2a ma zapisany model w `02-domain/`, oba zaakceptowane przez użytkownika
