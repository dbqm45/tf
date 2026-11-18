# Strategy, the test plan, reporting and escape analysis

## Basic distinctions
- **Verification** — "are we building the product right?" (conformance to the specification: reviews, automated tests).
  **Validation** — "are we building the right product?" (does it solve the need: UAT, tests with users, metrics after
  release — ux-feature-design, proc-product-discovery). A project can pass verification and fail validation.
- **Approach**: black box (behavior from the specification, without knowing the code — clean-room, qa-spec-first-testing),
  white box (paths in the code, branch coverage — the developer's unit tests), grey box (partial knowledge:
  the database schema, API contracts, logs — integration and exploratory tests).
- **Kinds of runs**:
  | Kind | Goal | Scope |
  |---|---|---|
  | smoke | is the build fit for testing at all, or is the deployment alive | a few critical paths, minutes |
  | sanity | does a specific fix work and did it not break its immediate surroundings | narrow, around the change |
  | regression | has nothing that worked before broken | wide, in layers (qa-regression) |
  | UAT | does the business accept the solution in its own scenarios | user scenarios, by them (qa-exploratory-manual) |
- **The tester's mindset**: ask what happens when an assumption does not hold (empty, too long, simultaneously, in the wrong
  order, without permissions, without a network); think like a user and like an attacker; report facts with evidence, not opinions;
  pragmatism — the depth of testing depends on risk, not on ambition.

## Testing in the development model
- **The V-model**: every stage of the specification has a matching test level (requirements ↔ acceptance, architecture ↔
  system and integration, module design ↔ unit); you design cases when the specification is created,
  not after the implementation. This rule works in agile work too.
- **Agile** (Scrum, Kanban, XP): quality is the responsibility of the whole team; the tester takes part in refining
  stories (Example Mapping — eng-testing), tests in the Definition of Done (proc-agile), automation in the same
  sprint as the feature.
- **Shift left**: review of requirements and design, tests before code (TDD/ATDD), static analysis and scans in the PR.
  **Shift right**: synthetic monitoring, flags and canary, production errors as a quality signal
  (qa-regression, `environment-and-special-data.md`).

## The test plan (`docs/project/05-plan/test-plan.md`)
Short and for this change or release, not a document for its own sake. Sections (consistent in idea with ISO/IEC/IEEE 29119-3):
1. **Scope**: what we test and what we do not (with a justification).
2. **Product risks** and priorities (SKILL.md: risk-based testing).
3. **Approach**: levels and kinds of tests, techniques, what we automate, what we do manually, non-functional requirements
   (performance — qa-performance-testing, accessibility, security).
4. **Environments and test data**; external dependencies and their stubs.
5. **Entry criteria** (e.g. the build passes smoke tests, the environment is ready) and **exit criteria** (e.g. no open
   critical defects, all high-risk cases executed, known issues accepted by the owner).
6. **Schedule, roles, deliverables** (the report, tickets, updated regression).
7. **Test project risks** (no data, an unstable environment) and a plan for them.

## The test report
- For the recipient: the decision ("do we release?") at the top — the state against the exit criteria, open risks, a recommendation.
- Numbers: executed / passed / failed / blocked by risk, defects by severity and state, coverage
  of **requirements** (every acceptance criterion has a result), known issues with acceptance.
- A technical report from CI: the JUnit XML format (every CI system reads it), HTML from Playwright or Allure (history, steps,
  screenshots, recordings, error categories). A report with personal data or secrets in screenshots does not leave the team.
- Quality metrics for learning, not for judging people: defects that escaped to production (and why), the time from
  report to fix, the share of unstable tests. "Defect density" and line coverage percentage are easy to
  game — do not make them targets.

## Escape analysis (defect RCA)
For every serious production defect, besides the fix:
1. The technical cause (5 × why, without looking for culprits — ops-sre-incidents).
2. **Why the tests did not catch it** — one of the categories: no requirement or an unclear requirement; the requirement existed,
   no case; the case was at the wrong level (e.g. only a unit test, and the bug in integration); the test existed,
   but the expected result came from the code (a mirror test — qa-spec-first-testing); a difference in environment or data; the test
   was unstable and ignored.
3. Action: a regression test at the right level (red first), a process change if the category repeats.

## Sources
- ISTQB Certified Tester Foundation Level Syllabus (v4.0); ISO/IEC/IEEE 29119-3 (test documentation)
- [roadmap.sh — QA](https://roadmap.sh/qa) (QA mindset, verification & validation, testing approaches, smoke, sanity,
  UAT, SDLC models, test planning, reporting, Allure, RCA)
Described in our own words.
