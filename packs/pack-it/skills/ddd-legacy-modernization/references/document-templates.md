# Templates of the A–C documents

Every document starts with a header: `title`, `created`, `type` (`domain-distillation` / `refactor-plan`), the commit
on which the code was analysed. At the end a summary of 5–8 sentences: what the artifact contains and the most important conclusion.

## A. `docs/project/02-domain/distillation.md`
```markdown
# Domain distillation — <product>, <date>, commit <sha>
**Constraints:** <e.g. no PRD — the README and the code are the source>

## Glossary
| Term | Definition | Source (document) | In the code | Other names |
|---|---|---|---|---|
| Generation session | a batch of proposals from one text, with a moment of finalization | `docs/prd.md:88` | BRAK w kodzie (only `generation_id` in `flashcards`) | "batch" (UI), "generation" (database) |

## Subdomains
| Area | Type | Justification (product goals) |

## Aggregate candidates
| Candidate | Invariant (quote) | Status: enforced / declared / ignored | Evidence |

## Model ↔ code divergences
| The document says | The code does | Evidence |

## Ranking
| # | Candidate | Value | Risk | Justification |
```

## B. `docs/project/02-domain/invariant-<name>.md`
```markdown
# Invariant: <rule> — the guardian aggregate plan
## List of invariants and axes
| Rule | Source | Coreness | Smearing (files/layers) | Enforcement |
## Diagnosis of the chosen one (all layers)
| Layer | Place | What it does with the rule | Problem (missing / inconsistent / UI only / swallows the error) |
## Design
- Root: `<Aggregate>`; methods with preconditions (signatures + pseudocode)
- Domain errors: `<ErrorName>` → mapping to a response (e.g. 409)
- Repository: `load(id)` / `save(aggregate)`; transaction: <scope>
- API route: parse → method → map the error
## Before / after (every current place of the rule)
## Phases (test-first) and test cases
| Operation | Input state | Expectation (success / named error) |
```

## C. `docs/project/02-domain/acl-<package>.md`
```markdown
# ACL for <package> — plan
## Dependencies and leak signals
| Package | Files that know it | Layers | Types in signatures/DTOs | Client/server |
## Choice (axes: reach · replacement cost · declared replaceability)
## Design
- Value object `<Name>`: mapping from/to persistence, conversion from/to the library type
- Port `<Name>` (domain language), adapter in `<directory>/`
## Proof of isolation
| File | Knows the package today | Knows it after the refactor |
## Completion criterion
`rg -l "<package>" src | rg -v '^<adapter-directory>/'` → empty; CI rule: <dependency-cruiser / ESLint / ArchUnit>
## Phases
```
