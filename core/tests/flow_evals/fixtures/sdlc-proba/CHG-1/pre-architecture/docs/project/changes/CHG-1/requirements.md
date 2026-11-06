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

**must** — na stronie prod w stopce widoczna data ostatniego wdrożenia, gdy flaga `show_last_deployed=true`.
- Given: odwiedzający otwiera stronę prod
- When: flaga `show_last_deployed` jest `true`
- Then: w stopce widzi datę ostatniego wdrożenia w formacie `RRRR-MM-DD`

### Stany błędu
- `config/build.json` nie istnieje → stopka pokazuje `—` (nie podnosimy błędu globalnego)
- flaga `show_last_deployed=false` → data ukryta (CHG-1/D2)
