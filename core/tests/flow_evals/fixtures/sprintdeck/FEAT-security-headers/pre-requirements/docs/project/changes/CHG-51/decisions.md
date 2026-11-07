---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
inputs: []
change: CHG-51
source: PRB-50
source_reported_at: 2026-11-04
---
# Decyzje zmiany CHG-51

## Bramka triage: approved
- ref: CHG-51/D1
- id: DEC-9001
- wyslano: tak
- kiedy: 2026-11-04
- kto: człowiek
- rodzaj: gate
- dlaczego: aplikacja publiczna (team.sprintdeck.app) bez CSP ani nagłówków bezpieczeństwa; PR #10 sprintdecka zatwierdza kierunek
- zrodlo: manual
- szkic: ai

## Bramka B1 intent: approved — wariant A
- ref: CHG-51/D2
- id: DEC-9002
- wyslano: tak
- kiedy: 2026-11-04
- kto: człowiek
- rodzaj: gate
- dlaczego: nagłówki bezpieczeństwa (CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy) przez middleware Next.js; CSP strict z nonce (najmniejsze ryzyko regresji dla istniejącego designu)
- zrodlo: manual
- szkic: ai
