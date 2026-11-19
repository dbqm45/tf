---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
inputs: []
change: CHG-3
source: PRB-27
source_reported_at: 2026-11-03
---
# Decyzje zmiany CHG-3

## Przyjmujemy PRB-27 do pracy jako zmianę: licznik „Wdrożenia w ostatnich 7 dniach: N" na stronie głównej, za flagą deploy_counter (off na prod na start).
- ref: CHG-3/D1
- id: DEC-0012
- sent: yes
- date: 2026-11-03
- by: dbqm45 (z góry, przebieg testowy A6, zatwierdził właściciel 2026-11-03)
- kind: triage
- why: Zgłoszenie opisuje realny brak miary wprost na stronie; proponowane rozwiązanie mieści się w aktualnej architekturze sdlc-proba (strona + istniejący odczyt /deployments).
- source: manual
- drafted_by: ai
