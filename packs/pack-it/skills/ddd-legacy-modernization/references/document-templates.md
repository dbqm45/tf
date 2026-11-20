# Document templates for the three diagnoses

> **Contents:** A. `docs/project/02-domain/distillation.md` · B. `docs/project/02-domain/invariant-<name>.md` · C. `docs/project/02-domain/acl-<package>.md`

Every document starts with the same header and ends with a summary of 5–8 sentences written for someone who reads only that.

```markdown
---
title: <what was diagnosed>
created: <YYYY-MM-DD>
type: domain-distillation | refactor-plan
commit: <short hash of the commit analysed>
---
```

Use `type: domain-distillation` for A and `type: refactor-plan` for B and C.

## A. `docs/project/02-domain/distillation.md`

```markdown
# Domain distillation — <system>

## Inputs and constraints
Documents read: … · Code areas read: … · Missing inputs (e.g. no PRD — README and code only): …

## Glossary
| Term | Definition | Documents (file:line) | Code (file:line or BRAK w kodzie) |
|---|---|---|---|

## Subdomains
| Subdomain | Kind (core / supporting / generic) | Why (product goal) |
|---|---|---|

## Aggregate candidates
| Candidate | Rule it protects (quote) | Status (enforced / declared / ignored) | Evidence |
|---|---|---|---|

## Model ↔ code divergences
| # | The document says | The code does | Evidence (file:line) |
|---|---|---|---|

## Ranking
| # | Area | Business value | Enforcement risk | Next (B / C / later) |
|---|---|---|---|---|

## Summary
```

## B. `docs/project/02-domain/invariant-<name>.md`

```markdown
# Rule: <the rule in one sentence>

## Candidate rules
| Rule | Closeness to core | Files / layers touching it | Enforcement (enforced / declared / violable) |
|---|---|---|---|
Chosen: … because …

## Where the rule lives today
| Layer | file:line | What happens (missing / inconsistent / UI only / trusts request / swallowed error) |
|---|---|---|

## Target design
Aggregate root, methods with preconditions, named domain error, repository, transaction boundary, route → error mapping.

## Before / after
| Place today | After the change |
|---|---|

## Phases (test first)
1. Characterisation tests of today's behaviour …

## Test cases
| Sequence | Expected |
|---|---|

## Summary
```

## C. `docs/project/02-domain/acl-<package>.md`

```markdown
# Isolating <package>

## Files that know the dependency today
Command used: `rg -l "from '<package>'" src/` (+ dynamic imports) · Count: … · Layers: …

## Ranking of leaks
| Dependency | Layers / files | Cost to replace today | Promised replaceable? (document:line) |
|---|---|---|---|

## Target design
Value object …, port …, adapter directory …, what the UI receives …

## Knows today / knows after
| File | Today | After |
|---|---|---|

## Completion check
Command: … → must list only files in `<adapter dir>`. CI rule: … (references/rule-templates.md)

## Summary
```
