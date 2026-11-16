---
artifact: plan
phase: plan
status: proposed
version: 1
author: tomasz
created: 2026-10-30
updated: 2026-10-30
inputs: [docs/project/changes/CHG-1/intent.md]
change: CHG-1
source: PRB-1
source_reported_at: 2026-10-30
tasks: [TSK-1, TSK-2]
---
# Plan zmiany CHG-1

Cięcia (TSK) — każde daje wartość samo i kończy się weryfikacją. Klucze cięć dopisz też do `tasks` w nagłówku,
a linię wydania (R1 = MVP) i flagę — do `release.yaml` (te same wartości co w kolumnach poniżej).

Rodzaj: „cięcie” (wartość: „użytkownik może …”) albo „fundament” (wartość: „(fundament) … jest gotowe”). Fundament
musi mieć w „Odblokowuje” cięcia tej zmiany (TSK), których wymaga; cięcie — dosłowne ID wymagań w „Wymagania”
(`US-02`, `FR-007`) albo weryfikację. To samokontrola planu cięć; `decision_record.py check` i REL-008 w ci_for_sdlc
sprawdzają ją tak samo.

| Cięcie | Rodzaj | Wydanie | Flaga | Wartość | Wymagania | Odblokowuje | Pliki | Weryfikacja |
|---|---|---|---|---|---|---|---|---|
| TSK-1 | fundament | R1 | — | (fundament) `config/build.json` z polem `deployedAt` jest gotowy do odczytu przez serwer | — | TSK-2 | `scripts/build-info.js`, `package.json`, `.gitignore` | `npm run build && node -e “const b=require('./config/build.json');if(!b.deployedAt)process.exit(1)”` → exit 0; `npm test` → 0 |
| TSK-2 | cięcie | R1 | show_last_deployed | użytkownik może zobaczyć datę ostatniego wdrożenia w stopce strony | — | — | `src/page.js`, `src/server.js`, `config/flags.prod.json`, `config/flags.test.json`, `test/page.test.js` | `npm test` → 0; manualne: GET `/` z `show_last_deployed: {enabled:true, rollout:100}` → stopka zawiera datę z `config/build.json` |

