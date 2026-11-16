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

Wpisy dodaje `decision_record.py decision add CHG-1 …` (po zatwierdzeniu szkicu przez człowieka). `id` nadaje rejestr
pdi (`record_decision` przez MCP) i wpisuje `decision mark`; bez serwera pdi zostaje puste, a `wyslano: nie` — wyślesz
później (`decision pending`). Nie wymyślaj numerów.

<!-- Wzór wpisu:
## <co zdecydowano, jedno zdanie>
- ref: CHG-1/Dn (nadaje decision add)
- id:
- wyslano: nie
- kiedy: RRRR-MM-DD
- kto: <osoba lub rola, która zdecydowała>
- rodzaj: product | technical | process | triage | intent | gate | other
- dlaczego: <1–5 zdań, tylko z rozmowy>
- zrodlo: claude-cli | claude-ai | slack | confluence | jira | manual
- szkic: ai | human
-->

## Bramka triage: approved
- ref: CHG-1/D1
- id: DEC-0001
- wyslano: tak
- kiedy: 2026-10-30
- kto: pdi
- rodzaj: gate
- dlaczego: decyzja w skrzynce bramek pdi (DEC-0001); uzasadnienie w rejestrze pdi
- zrodlo: manual
- szkic: human

## Bramka B1: approved
- ref: CHG-1/D2
- id: DEC-0002
- wyslano: tak
- kiedy: 2026-10-30
- kto: pdi
- rodzaj: gate
- dlaczego: decyzja w skrzynce bramek pdi (DEC-0002); uzasadnienie w rejestrze pdi
- zrodlo: manual
- szkic: human

## Bramka B2: approved
- ref: CHG-1/D3
- id: DEC-0003
- wyslano: tak
- kiedy: 2026-10-30
- kto: pdi
- rodzaj: gate
- dlaczego: decyzja w skrzynce bramek pdi (DEC-0003); uzasadnienie w rejestrze pdi
- zrodlo: manual
- szkic: human

## Bramka B3: approved
- ref: CHG-1/D4
- id: DEC-0004
- wyslano: tak
- kiedy: 2026-10-31
- kto: pdi
- rodzaj: gate
- dlaczego: decyzja w skrzynce bramek pdi (DEC-0004); uzasadnienie w rejestrze pdi
- zrodlo: manual
- szkic: human

## Bramka approve-for-implementation: approved
- ref: CHG-1/D5
- id: DEC-0006
- wyslano: tak
- kiedy: 2026-10-31
- kto: pdi
- rodzaj: gate
- dlaczego: decyzja w skrzynce bramek pdi (DEC-0006); uzasadnienie w rejestrze pdi
- zrodlo: manual
- szkic: human
