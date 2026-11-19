---
name: eng-code-audit
description: Use for a full code audit (architecture, security, quality, law) — scope, budget, parallel reviews.
metadata:
  catalog: "Use for a full code audit in several dimensions at once (architecture, security, quality and debt, tests, accessibility, usability, compliance with EU law) — scope and budget approved up front, a cheap scan on the cheapest model, parallel reviews with one implementer per dimension, merging duplicates, a ranking risk × reach ÷ cost of the fix, a report with evidence and a list of what was not checked. Not for an audit of technical debt alone (eng-tech-debt-audit) or a review of a single PR (qa-change-review)."
  review: "2027-10-18"
  keywords: "pełny audyt kodu, audyt aplikacji, przegląd całego kodu, audyt wielowymiarowy, audyt przed wdrożeniem, due diligence kodu, przejęcie projektu, audyt przed inwestycją, przeanalizuj cały kod, ocena jakości aplikacji, audyt bezpieczeństwa i dostępności, full code audit, application audit, review of the whole code, multi-dimensional audit, pre-deployment audit, code due diligence, project takeover, pre-investment audit, analyse the whole code, application quality assessment, security and accessibility audit"
---

# Full code audit

An audit in many dimensions at once, run like a project: the human approves the scope and budget, cheap tools do the
inventory, specialists assess in parallel, and the main session merges the results into one ranking with evidence. The audit fixes
nothing — it establishes, ranks and hands over.

## 1. Scope and budget (before any scan)
Show the human a proposal and wait for consent:
- **Dimensions** (choose the ones needed, not all of them out of momentum):

| Dimension | Implementer | Skills in the brief |
|---|---|---|
| architecture (`architecture`) | `architect` (analysis) or `tomasz-solution-architect` | arch-quality-attributes, eng-module-depth, ddd-connascence-analysis |
| security (`security`) | `security-reviewer` | sec-appsec-devsecops, be-auth-security, arch-threat-modeling |
| quality and debt (`quality`) | `specialist` | eng-tech-debt-audit, eng-clean-code |
| tests (`tests`) | `kasia-qa-analyst` | qa-test-design, qa-regression |
| accessibility (`accessibility`) | `natalia-accessibility-specialist` | ux-accessibility |
| usability (`usability`) | `natalia-product-designer` | ux-feature-design |
| front-end and browser performance (`performance`) | `specialist` | fe-web-platform, fe-architecture |
| compliance with EU law (`legal`) | `maja-product-compliance` | arch-eu-product-law, arch-privacy-compliance, sec-eu-regulations, ai-governance-compliance (when there is AI) |

- **Depth:**
  - *quick* (`quick`) — stage 0 and the 2–3 dimensions with the highest risk, implementers on `sonnet`;
  - *standard* — all the chosen dimensions on `sonnet`, a ranking, the top 10 with proposals;
  - *full* (`full`) — like standard, but architecture and security on `opus`, a large repo split into modules.
- **Cost limit:** an amount or a number of implementer calls, set by the human. You count it in the status bar or with
  `python3 .tf/factory/cost_report.py --days 1`; at 80% of the limit you stop and ask what to skip.
- **Boundaries:** what you do not touch (e.g. `vendor/`, generated code), whether you may run the project's tools, whether there is
  a test environment. You do not run active scans (DAST, a port scanner) against running systems without written
  consent (core-agent-security §5b).

**Running after consent:** the `/code-audit` workflow (`.claude/workflows/code-audit.js`) carries out stages 0–2
and the report. The arguments are the approved scope: `{"date": "YYYY-MM-DD", "dimensions": ["architecture", "security",
"quality", "tests", "accessibility", "usability", "performance", "legal"], "depth": "standard", "limit": 8,
"modules": [], "exclude": ["vendor/"]}` (optionally `executors`: dimension → agent, e.g. a persona from the table).
- The ranking, duplicates, blockers and hypotheses are computed by a script, without a model.
- A dimension without installed skills and a dimension over the limit go to "What was not checked".
- Implementers ask for consent to tools as usual; a longer run without questions needs `allow` rules.

Without the workflow (another tool, `disableWorkflows` turned on, contradictions to resolve along the way) you run
the stages by hand, as below.

## 2. Stage 0 — a cheap inventory (one `scout` implementer on `haiku` or the session itself)
Goal: one file with facts that all the reviewers get, so that none of them reads the repository from scratch.
1. `python3 .claude/hooks/detect_stack.py` — the stack and versions.
2. `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --hotspots --cochange` — hotspots.
3. `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py` (Python, TS/JS) — cycles and dependencies.
4. The tools the project **already has** (tests, lint, types, `npm audit`, scanners from CI) — the output to a file. No global
   installations; you record a missing tool as "not checked" rather than install it silently.
5. A map of modules and entry points (eng-codebase-mapping).
Result: `docs/project/07-review/<date>-code-audit-inventory.md` — the stack, modules, hotspots, tool results, what is missing.

## 3. Stage 1 — parallel reviews
- All the implementers in **one message** (separate contexts, a 5-minute cache).
- Each brief contains: the scope and modules, the inventory path, the skills to load, one question, the finding format
  and a limit (e.g. the 10 most important). Brief template: `references/report-template.md`.
- Finding format: ID · dimension · file:line · risk · reach · cost of the fix · evidence · proposal.
- "Nothing significant in this dimension" is a correct result; findings are not added for volume.
- An implementer that went beyond the scope or gave no evidence gets one follow-up question, not a new run from scratch.

## 4. Stage 2 — merging and ranking (the main session)
1. **Duplicates:** you combine findings with the same cause into one and keep all the dimensions as labels
   (e.g. missing input validation is both security and quality). The number of dimensions that reported it is a signal, not a multiplier.
2. **Evidence:** every finding has a file:line, a command output or a quote from a document. Without evidence you move the finding
   to the section "Hypotheses to check", outside the ranking.
3. **Ranking:** priority = risk (4 critical / 3 high / 2 medium / 1 low) × reach (3 the whole system or
   all users / 2 a module or a group / 1 a single place) ÷ cost of the fix (1 = S hours / 2 = M days / 4 = L weeks).
   Within the "quality and debt" dimension the order is already set by the eng-tech-debt-audit formula (with the change frequency).
4. **Blockers outside the ranking:** a leak of data or a secret, an authorisation bypass, a legal obligation with a deadline —
   they go to the top regardless of the score and straight to the human.
5. **Contradictions between implementers** (e.g. the architect wants to split a module, while security prefers one trust
   boundary) you show directly; the human decides, and a decision that is hard to reverse you record as an ADR.
6. **Handover:** architecture → ADR (arch-architect-practice); refactoring → eng-refactor-planning; missing
   tests → qa-test-design; security fixes → sec-appsec-devsecops; law → arch-eu-product-law (map of obligations),
   arch-privacy-compliance (RODO, the Polish name of the GDPR).
7. `python3 .claude/skills/core-grounding/scripts/grounding_check.py <report.md>` — the paths and references exist.

## 5. Report
The file `docs/project/07-review/<date>-code-audit.md` (core-project-record), the template in `references/report-template.md`:
1. TL;DR (≤ 7 points) and blockers.
2. The ranking (a table) and the top 10 with a change proposal (without carrying it out).
3. Quick wins: cost S with a risk of at least medium.
4. **What was not checked** — skipped dimensions, missing tools, modules outside the scope. Mandatory.
5. Contradictions and decisions for the human.
6. The audit cost against the budget (calls, models, the amount from `cost_report.py`).
A repeat audit compares with the previous report: RESOLVED, NEW, CHANGED.

## Rules
- One coherent question per implementer; you do not split one dimension between several of them without a split into modules.
- A large repo (over ~50 thousand lines or more than 5 modules) in full mode: a split into modules only in the dimensions
  that need it (quality, security); architecture always looks at the whole.
- You do not send code to external analysis services; facts about versions and regulations are checked by `researcher`.
- The code does not change during the audit; fixes are separate tasks after the ranking is accepted.

## Example
**Situation:** "We are taking over a SaaS application (Next.js + Python, about 40 thousand lines). A full audit before the contract, budget 15 USD."
**Result:**
- Scope approved: *standard*, 6 dimensions (without usability and performance), a limit of 8 implementer calls.
- Stage 0 on `haiku`: an inventory with 3 hotspots, no secret scanner in CI ("the git history was not checked for
  secrets").
- Stage 1: 6 implementers in one message, 41 findings; after merging 29 (12 duplicates, among others the same missing
  validation at api/orders.py:88 reported by security and quality).
- Blocker: no check of the resource owner at api/invoices.py:41 (risk 4, reach 3, cost S → 12, but a blocker anyway).
- Ranking: #2 missing labels in the payment form (app/checkout/form.tsx:23, 3 × 3 ÷ 1 = 9); #3 a cycle between
  the `billing` and `accounts` modules (3 × 2 ÷ 2 = 3).
- What was not checked: performance, usability, load tests. Cost: 7 calls, 11.40 USD out of 15.

## Checklist
- [ ] scope, depth and cost limit approved by the human before the scan
- [ ] stage 0 on the cheapest model; one inventory file for all the implementers
- [ ] reviews in one message; each brief with a question, skills, a format and a limit of findings
- [ ] duplicates merged; every finding with evidence, the rest in "Hypotheses"
- [ ] ranking risk × reach ÷ cost; blockers separately and straight to the human
- [ ] a "What was not checked" section and the cost against the budget in the report
- [ ] `grounding_check.py` without errors; handovers to ADR, refactoring and tests named

## Sources
- Anthropic, "How we built our multi-agent research system" (anthropic.com/engineering, 13.06.2025) — parallel
  subtasks with separate contexts, the token cost of multi-agent systems.
- Factory skills: eng-tech-debt-audit (finding format, repeat audit), core-cost-control (model cascade),
  core-problem-routing (an ad hoc team). Described in our own words.
