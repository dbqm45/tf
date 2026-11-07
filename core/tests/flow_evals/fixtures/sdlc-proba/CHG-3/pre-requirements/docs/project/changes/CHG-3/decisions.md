---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
inputs: []
change: CHG-3
---
# Decyzje zmiany CHG-3

## Przyjmujemy PRB-27 do pracy jako zmianę: licznik „Wdrożenia w ostatnich 7 dniach: N" na stronie głównej, za flagą deploy_counter (off na prod na start).
- ref: CHG-3/D1
- id: DEC-0012
- wyslano: tak
- kiedy: 2026-11-03
- kto: dbqm45 (z góry, przebieg testowy A6, zatwierdził właściciel 2026-11-03)
- rodzaj: triage
- dlaczego: Zgłoszenie opisuje realny brak miary wprost na stronie; proponowane rozwiązanie mieści się w aktualnej architekturze sdlc-proba (strona + istniejący odczyt /deployments). Ryzyko regresji ograniczone nową flagą deploy_counter, domyślnie off na prod. Przebieg testowy A6 — triaż accepted z góry zatwierdzony przez właściciela 2026-11-03.
- zrodlo: manual
- szkic: ai

