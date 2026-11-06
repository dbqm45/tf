---
artifact: plan
phase: plan
status: proposed
version: 1
author: tomasz
created: 2026-11-03
updated: 2026-11-03
inputs: [docs/project/changes/CHG-3/intent.md, docs/project/changes/CHG-3/requirements.md, docs/project/changes/CHG-3/architecture.md]
change: CHG-3
source: PRB-27
source_reported_at: 2026-11-03
tasks: [TSK-1]
---
# Plan zmiany CHG-3

## TL;DR
Jedno cięcie TSK-1 (R1 = MVP) za flagą `deploy_counter`: licznik „Wdrożenia w ostatnich 7 dniach: N” na stronie głównej.
Fundamentu nie ma: `node:sqlite`, tabela, indeks i mechanizm flag już istnieją (`src/deployments.js`, `src/flags.js`).
Podział na `countDeployments` i stronę dałby fundament bez własnej wartości, a całość to jedna akcja użytkownika.

Cięcia (TSK) — każde daje wartość samo i kończy się weryfikacją. Klucze cięć dopisz też do `tasks` w nagłówku,
a linię wydania (R1 = MVP) i flagę — do `release.yaml` (te same wartości co w kolumnach poniżej).

Rodzaj: „cięcie” (wartość: „użytkownik może …”) albo „fundament” (wartość: „(fundament) … jest gotowe”). Fundament
musi mieć w „Odblokowuje” cięcia tej zmiany (TSK), których wymaga; cięcie — dosłowne ID wymagań w „Wymagania”
(`US-02`, `FR-007`) albo weryfikację. To samokontrola planu cięć; `decision_record.py check` i REL-008 w ci_for_sdlc
sprawdzają ją tak samo.

| Cięcie | Rodzaj | Wydanie | Flaga | Wartość | Wymagania | Odblokowuje | Pliki | Weryfikacja |
|---|---|---|---|---|---|---|---|---|
| TSK-1 | cięcie | R1 | deploy_counter | użytkownik może zobaczyć na stronie głównej, ile wdrożeń środowiska było w ostatnich 7 dniach | US-01, FR-001, FR-002, FR-003, FR-004, FR-005, NF-001, NF-002, NF-003, NF-004, NF-005, NF-006 | — | `src/deployments.js`, `src/server.js`, `src/page.js`, `config/flags.test.json`, `config/flags.prod.json`, `test/deployments.test.js`, `test/page.test.js`, `test/server.test.js`, `test/server-errors.test.js`, `test/flags.test.js` | `npm test` → 0 (testy E-01A…E-05B napisane najpierw, czerwone przed kodem); `npm run lint` → 0; test wydajnościowy: 10 000 wdrożeń, flaga on → p95 `GET /` < 200 ms (sygnał, nie blokada); `config/flags.prod.json` → `deploy_counter.enabled == false` |

## Kolejność i zależności
Jedno cięcie, brak zależności. Gwiazda przewodnia (najmniejszy przepływ end-to-end dowodzący tezy) = samo TSK-1:
od `GET /` przez flagę i odczyt bazy do HTML.

## Etapy rolloutu flagi (zob. release.yaml)
1. `test` — flaga on od wdrożenia (FR-005); min. 3 dni, zero błędów 5xx w logu serwera, liczba zgodna z `/deployments`.
2. `prod` — włączenie `enabled: true, rollout: 100` osobną zmianą po decyzji właściciela flagi; to nie jest część TSK-1.
Po etapie 100%: PR usuwający flagę przed `remove_by`.

## Niewiadome
| Niewiadoma | Właściciel | Blokuje |
|---|---|---|
| właściciel flagi, data `remove_by`, kryterium wyjścia etapu `test` (wartości w release.yaml to [propozycja]) | właściciel aplikacji | nie (nie blokuje delivery TSK-1; blokuje włączenie na prod) |

## Poza zakresem MVP (kandydaci do R2, bez planowania teraz)
Rozróżnienie udane/nieudane, wykres/trend, konfigurowalne okno, nowy endpoint (intent.md, CHG-3/D2).

## Pytania do bramki
- Właściciel aplikacji sdlc-proba: kto jest właścicielem flagi `deploy_counter` (decyduje o przejściu etapów rolloutu) i czy `remove_by: 2027-02-28` w release.yaml (propozycja Tomasza) jest właściwą datą usunięcia flagi?
- Właściciel aplikacji sdlc-proba: jakie kryterium wyjścia z etapu `test` przed włączeniem na prod (propozycja w release.yaml: min. 3 dni na test, zero błędów 5xx w logu serwera i liczba zgodna z `/deployments` w spot-checku)?

## Przekazanie
Następny krok: faza design (tylko etykieta i miejsce w `<main>`), potem delivery TSK-1 metodą TDD.
