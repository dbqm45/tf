---
artifact: requirements
phase: definition
status: approved
version: 1
author: pdi
created: 2026-10-31
updated: 2026-10-31
inputs: [intent.md]
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
---
# Wymagania zmiany CHG-1

## FR-1 widoczność daty wdrożenia

**must** — stopka strony prod pokazuje datę ostatniego wdrożenia, gdy `show_last_deployed=true`.
- Given/When/Then jak w pre-architecture.
### Stany błędu
- brak `config/build.json` → stopka `—`
- flaga off → data ukryta
