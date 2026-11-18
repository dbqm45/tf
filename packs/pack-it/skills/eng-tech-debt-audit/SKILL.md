---
name: eng-tech-debt-audit
description: Use for a technical debt audit of a repo or module — findings with file:line, weight, effort, priorities.
metadata:
  review: "2027-10-09"
  catalog: "Use for a technical debt audit of a repository or module — orientation (size × change frequency), nine debt dimensions, a findings table with file:line, weight and effort, priority, quick wins, \"looks bad, but is fine\", a repeat audit. Not for a single refactoring (eng-behavior-preserving-refactoring) or the review of one PR (eng-design-principles)."
---

# Technical debt audit

An audit the team will act on: every finding points to a file and a line, has a weight, an effort and a proposal, and the result stays
in the repository and can be compared at the next audit. The audit rewrites nothing — it only establishes and proposes.

## Procedure
1. **Orientation (mandatory, before the assessment).**
   - README, manifests (`package.json`, `pom.xml`, `nx.json`), ADRs, the module map (eng-codebase-mapping).
   - History: `git log --oneline -200` and the changes from the last 6 months (`git log --since=6.months --stat`).
   - **Hot spots:** hotspot = **complexity × change frequency**. Each axis alone misleads: a dense but frozen file
     is merely old; a trivial but frequently changed one is usually configuration. Choose a cheap complexity proxy
     computed the same way across the whole repo (non-empty lines, indentation depth) — the product matters more than the choice of proxy.
     **Run** `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --hotspots --cochange`.
   - **Read co-changes in two ways:** a tight **pair** (A and B almost always together) is a hidden contract — a candidate for
     connascence of meaning or algorithm; a **hub** (a file changed together with many areas) is a wide reach. Co-changes
     lie both ways: bulk commits glue unrelated files together, and the absence of co-changes does not prove the absence of a contract
     (a backend model and its hand-made copy in the frontend, which do NOT change together, are silent debt to check).
   - Write down 1–2 paragraphs of the architecture model as you understand it. A discrepancy with the README is already a finding.
   - Show the human the audit plan (scope, modules, tools) before you start.
2. **Assessment in nine dimensions** (table below). You run only the tools that the project already has or that
   the human agrees to — no global installations.
3. **Merge and assess:** remove duplicates, assign weight and effort, compute the priority.
4. **Report** `docs/project/07-review/<date>-tech-debt.md` (core-project-record).

| Dimension | What you look for | Tools (TS / Java / Nx) |
|---|---|---|
| architecture decay | cycles, broken layers and module boundaries, files > 500 lines, logic duplicated in 3+ places, unused abstractions, dead code | `madge --circular`, `knip`, `nx graph`, Nx module boundary lint; jdeps, ArchUnit; Python and TS/JS without tools: `code_graph.py` from eng-codebase-mapping (runtime vs lazy cycles, pairs against the flow) |
| inconsistency | several ways of doing the same thing (HTTP, state, errors, names) | a review of patterns |
| types and contracts | `any`, `as`, unvalidated boundaries, API contracts without a schema | `tsc --noEmit` (strict), lint |
| tests | frequently changed files without tests, tests that check the implementation, flaky tests | coverage, CI history (qa-regression) |
| dependencies and configuration | known CVEs, unused packages, sprawl of environment variables | `npm audit`, `depcheck`/`knip`; OWASP dependency-check |
| performance | N+1, blocking I/O, unnecessary rendering | be-database, fe-architecture |
| errors and observability | swallowed exceptions, no logs and metrics on critical paths | ops-observability |
| security | secrets, no per-resource authorization, dangerous patterns | be-auth-security, ops-supply-chain-security |
| documentation | README and ADRs inconsistent with the code | docs-tech-writing |

## Assessment and priority
- **Weight:** critical / high / medium / low — by the effect (data, security, outage, slowing down the team).
- **Effort:** S (hours) / M (days) / L (weeks).
- **Priority (the factory's proposal):** weight (4/3/2/1) × the file's change frequency (changes in 6 months, min. 1) ÷ effort (1/2/4).
  Debt in code that nobody touches can wait; debt in a hot spot slows down every change.
- **Cheap debt and real debt:** mechanical coupling (generated code, regeneration, drift caught by the compiler
  or CI) looks dangerous, but is cheap — weight at most low. What is dangerous is dynamic coupling without a tool
  barrier (order, meaning at a long distance). In the description, name the kind (connascence), not "tightly coupled".
- Auxiliary label: Fowler's quadrant (deliberate / inadvertent × prudent / reckless). You first pay off the debt
  with the highest "interest" — the one that slows down current changes (the formula above computes this through the change frequency).
- You do not invent debt to fill the table: no findings in a dimension = "nothing significant".

## Report
1. Summary (≤ 10 points) and the architecture model.
2. Table: ID · dimension · file:line · weight · effort · priority · description · proposal.
3. Top 5 with a sketch of the change (a diff in brief, without executing it).
4. **Quick wins:** effort S with a weight of at least medium.
5. **Looks bad, but is fine** — mandatory: deliberate things, so that nobody "fixes" them. You justify the deliberateness
   with evidence: an ADR, a commit (`git log -L :<function>:<file>`, `git blame`), a PR description; the number of fixes
   of the mechanism in the history is also evidence (e.g. 0 in 6 years). You close the risk of a deliberate limitation with a cheap guard
   (a test, a linter rule), not with a rebuild. Choosing what and how to refactor: eng-refactor-planning.
6. Questions for the team (when context is missing, you ask instead of guessing).

## Large repositories and a repeat audit
- Over ~50 thousand lines or more than 5 modules: one executor per module (each with the same procedure), then merging
  and a shared ranking.
- A repeat audit compares with the previous report: you mark findings as ROZWIĄZANE (resolved), NOWE (new) or ZMIENIONE (changed).
- Mark deliberate shortcuts in the code with a comment `debt: <limitation>, <when to come back>`; the audit collects them into the table,
  and a marker without a return condition is a separate finding.

## Architecture garbage collection as a routine
An audit once a quarter does not keep up with code written with agents. The loop:
1. **Architecture tests** (layers, cycles, file size; tools such as dependency-cruiser, import-linter, Tach,
   ArchUnit — ddd-legacy-modernization) in the fast gates and in CI; the agent runs them before "done".
2. **Ratchet:** the threshold starts at the current maximum and only goes down; exceptions are narrow, with an owner
   and a deadline.
3. **A weekly routine:** one violation → one small refactoring PR with a human review
   (core-async-delegation §5).
4. Architecture tests, thresholds and exception lists in **protected paths** (CODEOWNERS and branch protection): an agent
   optimizing for "green CI" will move the verifier instead of the code.

## Example
**Situation:** "An audit of `apps/shop-api` before a clean-up sprint — where to start?"
**Result** (after the orientation and the plan shown to the human):

| ID | file:line | Weight | Effort | Changes | Priority |
|---|---|---|---|---|---|
| D2 | `src/billing/invoice.ts:88` (VAT without tests) | high | M | 25 | 3×25÷2 = 37.5 |
| D3 | `src/payments/webhook.ts:42` (`catch {}`) | critical | S | 6 | 4×6÷1 = 24 |

Quick win: D3. "Looks bad, but is fine": two `retry.ts` files — deliberately (ADR-007).
More examples: `references/examples.md`.

## Checklist
- [ ] orientation and the architecture model before the assessment; the plan shown to the human
- [ ] every finding with file:line, weight, effort and a proposal
- [ ] hotspots as complexity × frequency; co-changes as pairs and hubs; cheap debt separated from dangerous debt
- [ ] the priority takes the change frequency into account; quick wins listed
- [ ] the "looks bad, but is fine" section
- [ ] report in docs/project/07-review/, comparison with the previous one

## Sources
- The 10xDevs course, ed. 3 (2026), module 4, lessons 3–4 (hotspots, co-changes, cheap and dangerous debt, intent from history,
  the debt quadrant) — training material (accessed 2026-10-09); described in our own words.

## Sources of inspiration
[tech-debt-skill](https://github.com/ksimback/tech-debt-skill) (orientation through size and change history, debt
dimensions, the findings table, the section of deliberate things, splitting into modules, a repeat audit) and
[ponytail](https://github.com/DietrichGebert/ponytail) (markers of deliberate shortcuts with a return condition) — described
in our own words; the priority formula and the Java/Nx tools were added in the factory.
