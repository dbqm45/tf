---
name: qa-test-design
description: Use when designing test cases and a test plan — equivalence classes, boundaries, decision tables, states, risk.
metadata:
  review: "2027-10-09"
  catalog: "Use when designing test cases and a test plan in any technology — equivalence classes, boundary values, decision tables, state transitions, pairwise tests, risk-based testing, choosing the test level, the format of a case with the expected result and its source. Not for writing test code (tool-*)."
  keywords: "strategia testów dla całego projektu, projekt prawie bez testów, od czego zacząć testy, co ma się znaleźć w strategii testów, aplikacja z AI, asystent AI w aplikacji, awarie poza modelem, przypadki testowe dla agenta, text-to-SQL, integracja z Google Drive, paginacja w testach, endpoint listy z paginacją, test sprawdza tylko pierwszą pozycję, dane wielu najemców w testach, test strategy for the whole project, a project with almost no tests, where to start with tests, what a test strategy should contain, an application with AI, an AI assistant in the app, failures outside the model, test cases for an agent, Google Drive integration, pagination in tests, a list endpoint with pagination, the test checks only the first item, multi-tenant data in tests"
---

# Test design

## Techniques — when to use which
| Technique | When | How |
|---|---|---|
| **Equivalence classes** | input data with ranges/categories | split into valid and invalid classes; one case per class |
| **Boundary values** | every range and threshold ("from 10 units") | test **the boundary, just below and just above** (9, 10, 11) and min/max/0/empty |
| **Decision table** | several conditions give different results (discounts, permissions) | a column = a combination of conditions → the expected action; remove impossible combinations |
| **State transitions** | an object has states (a reservation, an order, a lock from the Availability archetype) | a state diagram → test every allowed transition **and** a disallowed one (it should be rejected) |
| **Pairwise tests** | many configuration parameters (browser × role × language) | a set covering every pair of values instead of the full product |
| **Scenarios / use cases** | end-to-end user flows | the main path + alternative + error paths |
| **Error guessing** | a supplement to the above | empty values, duplicates, special characters, time zones, concurrency, a double click, network loss |
| **Pagination and isolation edge** | lists with a page limit, multi-tenant data | the number of results equal to the page limit → check the next page; test data: more records than one page, records of a second tenant, an access-denied case; an assertion on the **whole** set computed from independently seeded data, not on the status and the first row |

## Priority — risk-based testing
Risk = **impact** (money, data, security, reputation) × **probability** (complexity, novelty, bug history).
High risk → more techniques, lower test levels, mutation tests; low → a single test of the main path.

## The test level — "as low as possible, as cheap as possible"
| What you check | Level |
|---|---|
| a business rule, a calculation, validation, a state transition | **unit** (domain logic, no framework) |
| cooperation with a database, queue, external API | **integration** (real dependencies, e.g. test containers) |
| contract conformance between services/the front end and the API | **contract** |
| a UI component with interaction | **component** (e.g. a browser in Vitest) |
| a critical user path through the whole system | **e2e** (few) |
| appearance | **visual** (screenshots), accessibility — **automatic (axe) + manual** |
The same case should not be tested at all levels — pick the lowest one that checks it reliably.

## The test case format
| ID | Requirement | Technique | Preconditions | Steps / input | **Expected result** | **Source of the result** | Level | Priority |
|---|---|---|---|---|---|---|---|---|
| TC-014 | H1-AC2 | boundary values | an empty cart | 10 pcs × PLN 20.00 | PLN 190.00 (5% discount) | requirements.md: "from 10 units inclusive 5%" | unit | H |
The **Source of the result** column is mandatory (qa-spec-first-testing). No source = an open question, not guessing.

## Non-functional requirements (the minimum)
- **Accessibility**: an automatic scan (axe) + manually the keyboard, focus, a screen reader for key paths.
- **Performance**: a smoke test of response times for the (H,H) scenarios from arch-quality-attributes.
- **Security**: input validation, authorization per resource (a test for 403 on someone else's resource), no sensitive data in responses.

The strategy and the test plan (verification vs validation, black/white/grey box, smoke, sanity, regression, UAT, the V-model
and agile work, entry and exit criteria, the test report, defect escape analysis): `references/test-strategy-and-plan.md`.
Performance tests: qa-performance-testing.
An AI application (model tools, integrations, text-to-SQL): besides model evals, nine classes of failure that are not
the model's fault, with a test for each — `references/ai-application-beyond-the-model.md`.

## Output
`docs/project/05-plan/test-plan.md` (the core-project-record template): scope, risks, techniques, levels, cases (or a link to
the file with the cases), entry/exit criteria, the split into automated and manual tests.

A project with no tests or with tests "where it is easy": first the **project test strategy**
(`docs/project/05-plan/test-strategy.md`, the template `templates/test-strategy.md`, the procedure
`references/project-test-strategy.md`) — an interview with the human, a risk map with sources, rollout phases, gates,
recipes, exclusions. The change's test plan draws on it and updates it at the end.
