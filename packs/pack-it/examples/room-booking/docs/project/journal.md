---
artifact: journal
phase: meta
status: accepted
version: 1
author: system
created: 2026-09-27
updated: 2026-09-27
inputs: []
---
# Project journal
<!-- Append only. The easiest way: python3 .claude/hooks/project_record.py log --by <who> --phase <phase> "<what and why>" -->

| When | Who | Phase | Event |
|---|---|---|---|
| 2026-09-27 08:09 | system | meta | Created the project record (docs/project/) |
| 2026-09-27 08:15 | tomasz | architecture | Stack recommendation (proposed): a modular monolith Java 25/Spring Boot 4.1 + Angular 22 + PostgreSQL 18 on App Service in an EU region; ADR-0001..0004, D-001..D-005; waiting for the user's acceptance and IT's answers (04-architecture/stack-decision.md) |
| 2026-09-27 08:16 | user | architecture | Accepted stack-decision v1 and ADR-0001..0004; IT confirms: the rooms are not Exchange mailboxes, the M365 admin consent will be given |
| 2026-09-27 08:18 | jan | plan | Delivery plan (proposed): 8 steps, walking skeleton -> H6 -> tactical design of the Allocation aggregate -> H1 (without M365) -> H5/H2/H3/H4 -> M365 integration (blocked by IT's answer); 05-plan/plan.md |
