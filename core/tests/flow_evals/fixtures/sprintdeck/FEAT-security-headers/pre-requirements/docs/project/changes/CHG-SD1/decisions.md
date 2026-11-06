---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
inputs: []
change: CHG-SD1
source: PRB-SD-10
source_reported_at: 2026-11-04
---
# Decyzje zmiany CHG-SD1

## Bramka triage: approved
- ref: CHG-SD1/D1
- id: DEC-SD-0001
- wyslano: tak
- kiedy: 2026-11-04
- kto: człowiek
- rodzaj: gate
- dlaczego: aplikacja publiczna (team.sprintdeck.app) bez CSP ani nagłówków bezpieczeństwa; PR #10 sprintdecka zatwierdza kierunek
- zrodlo: manual
- szkic: ai

## Bramka B1 intent: approved — wariant A
- ref: CHG-SD1/D2
- id: DEC-SD-0002
- wyslano: tak
- kiedy: 2026-11-04
- kto: człowiek
- rodzaj: gate
- dlaczego: nagłówki bezpieczeństwa (CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy) przez middleware Next.js; CSP strict z nonce (najmniejsze ryzyko regresji dla istniejącego designu)
- zrodlo: manual
- szkic: ai
