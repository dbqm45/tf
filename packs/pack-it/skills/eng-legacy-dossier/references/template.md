# Legacy system dossier template

Contents: 1. Index `README.md` · 2. Module card `modules/<module>.md` · 3. Where to get business rules from ·
4. Contract for `dossier_check.py`

## 1. Index `README.md`

```markdown
<!-- legacy-dossier -->
# System dossier: <name>
System: <name> · Commit: <HEAD> · Date: <YYYY-MM-DD>

## TL;DR
<5–7 sentences: what the system does for the business, how many modules it consists of, where the core is, the biggest risk of change,
how many `to verify` rules.>

## Modules
| Module | Purpose | State |
|---|---|---|
| [invoices](modules/invoices.md) | issuing invoices and corrections | yellow |

## Flows
### Issuing an invoice
1. `InvoiceController.create` (src/web/InvoiceController.java:40) accepts the order …
(Mermaid sequence diagram)

## Glossary
| In the code | In the business | Note |
|---|---|---|
| `Doc` | invoice | also a correction (`type = 'K'`) |

## State and refactoring candidates
| Module | State | Candidate | Why (evidence) |
|---|---|---|---|
| invoices | yellow | one place for rounding | R-FAK-01 vs R-FAK-02 |

## Open questions
- <question> — whom to ask (an area, not an assessment of a person)

## Limitations
<what the dossier does not cover: skipped modules, no access to the production database, generated code>

## Handoff
<for eng-tech-debt-audit / eng-refactor-planning: which candidates to start with>
```

## 2. Module card `modules/<module>.md`

```markdown
<!-- legacy-dossier:module -->
# Module: <name>
State: green|yellow|red — <reason in one sentence>

## Purpose
## Responsibilities
## Inputs and outputs
## Business rules
| ID | Rule | Evidence | Confidence |
|---|---|---|---|
| R-<MOD>-01 | <a sentence for the business> | path/File.java:42 | test|code|to verify |
## Data
## Dependencies
## Pitfalls
## Tests
## Questions
```

- A rule ID is unique across the whole dossier: `R-<module abbreviation>-<number>`.
- Evidence: a path relative to the repository directory, `file:line` or `file:from-to`; several pieces of evidence separated by commas.
- No evidence: `—` and the confidence `to verify`, and the question goes to the Questions section.

## 3. Where to get business rules from

| Place in the code | What it usually hides | Example |
|---|---|---|
| conditions with numbers and dates | thresholds, deadlines, limits | `if (days > 30)` → payment deadline |
| validations and error messages | necessary conditions | `"Amount must be positive"` |
| domain exceptions | forbidden states | `InvoiceAlreadyPaidException` |
| `WHERE` / filters in queries | who and what is "active" | `status <> 'ARCH' AND deleted = 0` |
| enums and constants | states and transitions | `DRAFT → ISSUED → PAID` |
| flags and configuration | variants for customers or countries | `vat.reverse-charge.enabled` |
| test names | behaviour confirmed by a test | `shouldRejectCorrectionAfterPayment` |
| git history (`git log -S`, "fix" descriptions) | rules added after an incident | "fix: correction after payment" |
| triggers and procedures in the database | rules outside the application code | `BEFORE UPDATE ON invoices` |

A rule from a test has the confidence `test`. A rule from the code alone — `code`. An inference from a name, a comment or the history without
confirmation in the code — `to verify`. When the test and the code say different things, write down both versions and a question.

## 4. Contract for `dossier_check.py`

- First line of the index: `<!-- legacy-dossier -->`, of the cards: `<!-- legacy-dossier:module -->`.
- Index sections: TL;DR, Modules, Flows, Glossary, State and refactoring candidates, Open questions, Limitations.
- Card sections: Purpose, Responsibilities, Inputs and outputs, Business rules, Data, Dependencies, Pitfalls, Tests,
  Questions; the line `State: <green|yellow|red> — <reason>`.
- A module in the index without a file and wrong evidence is an error; a card outside the index — a warning.
