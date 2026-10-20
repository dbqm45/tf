---
artifact: decisions
phase: meta
status: accepted
version: 1
author: system
created: 2026-09-27
updated: 2026-09-27
inputs: []
---
# Rejestr decyzji

| ID | Data | Decyzja | Uzasadnienie (1 zdanie) | Status | Autor | Szczegóły |
|---|---|---|---|---|---|---|
| D-001 | 2026-09-27 | Styl: modularny monolit (Spring Modulith), jedna jednostka wdrożenia | 1 zespół, MVP 3 mies., żaden scenariusz nie wymaga niezależnego skalowania; jedna transakcja ACID dla rezerwacji i outboxa | accepted | tomasz | [ADR-0001](04-architecture/adr/0001-modularny-monolit.md) |
| D-002 | 2026-09-27 | Stack: Java 25 + Spring Boot 4.1, Angular 22 + MSAL Angular, PostgreSQL 18 | kompetencje zespołu i najmniej technologii; wersje wspierane w horyzoncie MVP | accepted | tomasz | [stack-decision](04-architecture/stack-decision.md) |
| D-003 | 2026-09-27 | Spójność rezerwacji: exclusion constraint (zasób, przedział) w PostgreSQL, rezerwacje i blokady w jednej tabeli | gwarancja „0 podwójnych” w bazie, niezależnie od ścieżki kodu | accepted | tomasz | [ADR-0002](04-architecture/adr/0002-spojnosc-rezerwacji-postgresql-exclusion-constraint.md) |
| D-004 | 2026-09-27 | Hosting: App Service Linux + PostgreSQL Flexible GP, jeden region UE (Poland Central po weryfikacji S0) | najprostsza obsługa; 99,5% w godz. 7–19 bez HA multi-region | accepted | tomasz | [ADR-0003](04-architecture/adr/0003-hosting-app-service-region-ue.md) |
| D-005 | 2026-09-27 | M365: Graph z uprawnieniami aplikacyjnymi (RBAC for Applications), outbox, sync w jedną stronę | rezerwacja nie zależy od dostępności Graph; warunkowe — czeka na odpowiedź IT | accepted | tomasz | [ADR-0004](04-architecture/adr/0004-integracja-m365-graph-outbox.md) |
