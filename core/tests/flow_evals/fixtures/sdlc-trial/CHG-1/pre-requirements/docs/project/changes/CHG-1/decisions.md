---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
created: 2026-10-30
updated: 2026-10-31
inputs: []
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Decyzje zmiany CHG-1

## Bramka triage: approved
- ref: CHG-1/D1
- id: DEC-0001
- sent: yes
- date: 2026-10-30
- by: pdi
- kind: gate
- why: zgłoszenie PRB-1 przyjęte w pdi
- source: claude-cli
- drafted_by: ai

## Bramka B1: approved — wariant A
- ref: CHG-1/D2
- id: DEC-0002
- sent: yes
- date: 2026-10-31
- by: człowiek
- kind: gate
- why: wariant A (data wdrożenia w stopce za flagą show_last_deployed) rozwiązuje problem zaufania
  odwiedzającego; warianty B i C wymagają narzędzi deweloperskich
- source: claude-cli
- drafted_by: ai
- question: Czy flaga ma być on/off per odwiedzający czy globalna?
- answer: globalna, bo mamy jeden rollout do prod
