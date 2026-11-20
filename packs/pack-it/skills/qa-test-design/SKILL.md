---
name: qa-test-design
description: Use when designing test cases and a test plan — equivalence classes, boundary values, decision tables, states, risk, test level, source of expected result.
metadata:
  review: "2027-10-09"
  catalog: "Use when designing test cases and a test plan in any technology: choosing techniques (equivalence classes, boundary values, decision tables, state transitions, pairwise, scenarios, error guessing, pagination and tenant isolation), risk-based priority, the test level, the case format with a mandatory source of the expected result, a minimal non-functional check; also a risk-driven test strategy for a whole project with few tests, application-side failure classes of AI features, the test plan, the report and escape analysis. Not for runner or framework syntax (tool-playwright, tool-vitest, tool-pytest), where expected values come from and clean-room roles (qa-spec-first-testing), regression suite upkeep (qa-regression), exploratory sessions (qa-exploratory-manual) or load tests (qa-performance-testing)."
  keywords: "strategia testów dla całego projektu, projekt prawie bez testów, od czego zacząć testy, co ma się znaleźć w strategii testów, aplikacja z AI, asystent AI w aplikacji, awarie poza modelem, przypadki testowe dla agenta, text-to-SQL, integracja z Google Drive, paginacja w testach, endpoint listy z paginacją, test sprawdza tylko pierwszą pozycję, dane wielu najemców w testach, test strategy for the whole project, a project with almost no tests, where to start with tests, what a test strategy should contain, an application with AI, an AI assistant in the app, failures outside the model, test cases for an agent, Google Drive integration, pagination in tests, a list endpoint with pagination, the test checks only the first item, multi-tenant data in tests"
---

# Test design — techniques, priority, level, case format

Input: a requirement (acceptance criterion, business rule, contract, backlog item). **No requirement given** → ask for the source; any case
written anyway gets its expected value marked as an open question, never a guess. Where expected values may come from and who
may look at the code: qa-spec-first-testing.

## 1. Pick techniques for the requirement
| The requirement has… | Technique | What you write |
|---|---|---|
| ranges or categories of input | **equivalence classes** | one case per valid and per invalid class |
| a numeric threshold | **boundary values** | at, just below, just above (9 / 10 / 11), plus min, max, zero, empty |
| several conditions combined | **decision table** | one column per combination of conditions; drop impossible combinations explicitly |
| statuses and events | **state transitions** | a state diagram; every allowed transition, at least one illegal transition that must be rejected, self-transitions |
| many configuration parameters | **pairwise** | every pair of values covered (a generator), not the full product |
| a user flow | **scenarios** | the main path, alternative paths, error paths |
| any input from people or systems | **error guessing** | empty, duplicates, special characters and Unicode, time zones and DST, concurrency, double click, network loss |
| a list with paging or multiple tenants | **pagination and isolation** | see §2 |

Use several techniques on one requirement when the risk is high; one main-path case when it is low.

## 2. Lists, paging, tenants
A test that creates 3 records and checks `200` plus the first row proves almost nothing. For a list endpoint with a page limit L:
- seed **more than one page** (L + 1, e.g. 51 for 50 per page) and check the next page and the end of the list;
- seed a **second tenant** (another organization) with its own data; none of it may appear;
- add a denied-access case (a user from tenant B asking for tenant A's id → 403/404);
- assert on the **whole set**: ids and count computed from the independently seeded test data, not "status + first item",
  and never from the implementation's own query.

## 3. Priority by risk
Risk = impact × probability. High risk: more techniques, more cases at lower levels, mutation testing on that module
(qa-spec-first-testing). Low risk: one main-path test. Write the risk next to the case so the order of work is visible.

## 4. Choose the level
The lowest level that checks the case reliably and cheaply:
- a rule, calculation, validation, state transition → **unit**;
- a database, queue, external API → **integration** with real dependencies (containers), not mocks of them;
- an agreement between services → **contract** tests;
- an interactive UI component → **component** level (tool-vitest browser mode);
- a few critical user journeys → **e2e** (tool-playwright), not every rule;
- visual appearance → **visual** comparison;
- accessibility → an automatic scan plus a manual pass with the keyboard and assistive technology.
Do not test the same case at every level. A state machine is tested at unit level; e2e covers one or two happy journeys through it.

## 5. Case format
| ID | Requirement | Technique | Preconditions | Input | Expected | Source of the result | Level | Priority |
|---|---|---|---|---|---|---|---|---|

The **source of the expected result** is mandatory: a criterion id, a quote, a hand calculation. Empty → an open question to the
requirement owner. Case ids `TC-014`, requirement refs like `H1-AC2` or `US-02/AC-3`. The plan goes to
`docs/project/05-plan/test-plan.md` (the core-project-record `test-plan` template).

## 6. Minimal non-functional check
- **Accessibility**: axe (or the stack's scanner) on key pages, plus manual keyboard navigation and an assistive-technology pass (NVDA, VoiceOver).
- **Performance**: a smoke test of high-risk scenarios (response time under a modest load); real load tests → qa-performance-testing.
- **Security**: input validation at boundaries; authorization per resource, including a **403 on someone else's resource**;
  no sensitive data in responses, errors or logs. Threats in depth → arch-threat-modeling, be-auth-security.

## 7. Beyond one change — references
- **Test plan, report, exit criteria, escape analysis** (V-model, verification vs validation, smoke/sanity/regression/UAT,
  plan sections per ISO/IEC/IEEE 29119-3, a report that starts with the decision, why a production defect escaped):
  `references/test-strategy-and-plan.md`.
- **A test strategy for a whole project** with no or few tests (inputs, risk map, response per risk, rollout phases,
  quality gates, what we knowingly do not test): `references/project-test-strategy.md`; the document is written from
  `templates/test-strategy.md` to `docs/project/05-plan/test-strategy.md`.
- **AI-backed features** — failure classes on the application side: `references/ai-application-beyond-the-model.md`
  (answer quality itself → ai-evals).

## Example
Requirement H1-AC2: "5% discount from 10 items, 10% from 50 items, business accounts only."

Boundaries: 9 / 10 / 11 and 49 / 50 / 51. Decision table:

| Condition | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| business account | yes | yes | yes | no |
| quantity | < 10 | 10–49 | ≥ 50 | any |
| discount | 0% | 5% | 10% | 0% |

| ID | Requirement | Technique | Input | Expected | Source of the result | Level | Priority |
|---|---|---|---|---|---|---|---|
| TC-011 | H1-AC2 | boundary | business, 9 × 100.00 | 900.00 | H1-AC2, hand calc | unit | high |
| TC-012 | H1-AC2 | boundary | business, 10 × 100.00 | 950.00 | H1-AC2, 1000 × 0.95 | unit | high |
| TC-013 | H1-AC2 | boundary | business, 50 × 100.00 | 4500.00 | H1-AC2, 5000 × 0.90 | unit | high |
| TC-014 | H1-AC2 | decision table R4 | private, 50 × 100.00 | 5000.00 | H1-AC2 "business only" | unit | high |
| TC-015 | H1-AC2 | error guessing | business, 0 items | validation error | open question to the PO — not in H1 | unit | medium |

Plus TC-016..TC-018 for 11, 49 and 51, and at most one e2e journey (checkout showing the discount).

## Sources
- ISTQB Certified Tester Foundation Level Syllabus v4.0 (2023), chapter 4 — black-box techniques (equivalence partitioning,
  boundary value analysis, decision tables, state transition testing), experience-based techniques (error guessing), risk-based testing.
- ISO/IEC/IEEE 29119-4:2021 — test techniques, incl. pair-wise (combinatorial) testing; ISO/IEC/IEEE 29119-3:2021 — test documentation.
