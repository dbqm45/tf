---
name: docs-tech-writing
description: Use for technical documentation in the repo — when and how to write an ADR, README, API, CHANGELOG, runbook, manual; structure, style, review.
metadata:
  review: "2027-10-17"
  catalog: "Use when writing, fixing or assessing technical documentation in the repo — README, API documentation, ADR, CHANGELOG, runbook, manual, module/feature description; audience, structure, style, process and review. Not for the project record artifacts in docs/project/ (core-project-record), commit messages (core-conventional-commits) or code comments."
  keywords: "kiedy pisać ADR, dokumentować decyzję, dokumentacja, README, runbook, instrukcja, opis modułu, when to write an ADR, document a decision, documentation, user manual, module description, technical writing, does it deserve an ADR, when to write an ADR, skip the ADR, architecture decision record"
---

# Technical documentation

## Before you start — two questions
1. **For whom?** A UI user ≠ a developer extending the system (different content, style, vocabulary). Without other hints,
   write for a developer who deploys/integrates. Several groups with different needs → separate documents or clearly
   marked sections.
2. **Descriptive or task-based?** Descriptive (the order of the system's elements) → reference, API. Task-based (the order of the
   reader's work) → manuals, tutorials.

## General rules
- The reader is busy: the most important things first, then the details. Many small chapters > a few large ones.
- **Structure first** (chapters → subchapters), then fill in the nodes — do not write linearly.
- **KISS:** short sentences and paragraphs; steps as a numbered list, comparisons as a table, not comma-separated lists.
  Runbook, installation, repair steps: ASD-STE100 rules — one action per step, a sentence up to about 20 words,
  a warning before the step (`references/style-and-structure.md`).
- **Consistent terms matter more than elegance** — once "system", always "system"; the same for formatting.
  When a style rule conflicts with clarity, choose clarity.
- Every command/method/endpoint with a **code example** that can be copied and run (blocks with a language, ```bash).
  Examples from the simplest to the hard ones.
- Data in examples and screenshots: realistic but **made up**; never real people's data or real secrets.
- One fixed marker for places to fill in (`TBD`) — one search finds them all.
- Documentation lives next to the code and changes in the same commit as the code (`docs:` — core-conventional-commits).
  Generate reference documentation from the sources when you can (OpenAPI, TypeDoc/JSDoc).

## Which document
| Need | Document | Notes |
|---|---|---|
| Entry to the repo/package | README | skeleton below |
| Architecture decision | ADR | in `docs/project/` the template from core-project-record |
| Changes for users of a version | CHANGELOG | Keep a Changelog or generated (`nx release`) |
| Reaction to an alert | runbook | Symptom → confirmation → fix → rollback → escalation |
| HTTP contract | API documentation / OpenAPI | update the spec, not a separate document |
| A user's work with the system | manual | task-based; table of contents, glossary, index |
| First success, learning | tutorial / quick start | Diátaxis: `references/documentation-types.md` |
| A practitioner's specific goal | how-to guide | as above |
| Changes for users (not developers) | release notes | what is new, what to do, breaking changes; as above |
| Error, symptom | troubleshooting / error list | by symptom; as above |
| Article, comparison, case study | technical content outside documentation | `references/technical-content-and-seo.md` |
| Project phase artifacts (brief, requirements, plan…) | — | **core-project-record**, not here |

## README — skeleton
1. One sentence: what it is and for whom.
2. Quick start (≤ 5 commands to a working state).
3. Configuration (table: variable | default | description) — only placeholders for secrets.
4. Typical tasks (test, build, deploy).
5. Directory structure (key ones only).
6. Where to find help / how to contribute.

## ADR — `docs/project/04-architecture/adr/NNNN-short-title.md`
**Threshold — all three at once:** (1) hard to reverse, (2) without context it will surprise a future reader ("why like this?"),
(3) there was a real choice between alternatives. Any of them missing → no ADR (a row in `decisions.md` or nothing is enough).
These qualify: the shape of the architecture, the way contexts integrate, a technology with lock-in (database, queue,
identity provider — not every library), decisions about data boundaries and ownership (also an explicit "no"), deliberate
departures from the obvious path, constraints invisible in the code (law, contracts, performance requirements), a rejected
alternative if the reason is not obvious. An ADR may be one paragraph — what counts is *that* and *why*. You **propose** an ADR,
you do not create it on your own; rejecting a candidate for a lasting reason is also worth recording, so that it does not come back.
In projects with a record (`docs/project/`) use the template `core-project-record/templates/adr.md` (with a YAML header)
and add a row to `decisions.md`. Outside the record this is enough:
```markdown
# NNNN. Decision title
Status: Proposed | Accepted | Superseded by NNNN
Date: YYYY-MM-DD
## Context
What problem, what constraints.
## Decision
What we choose (1–3 sentences).
## Considered options
- Option A — pros / cons
- Option B — pros / cons
## Consequences
What we gain, what we lose, what needs to be done next.
```

## CHANGELOG, runbook, API
- **CHANGELOG** (Keep a Changelog): sections in `## [Unreleased]`: Added, Changed, Deprecated, Removed, Fixed, Security.
  An entry = one line from the user's perspective. With `nx release` the changelog comes from the commits — watch their format.
- **Runbook:** for every alert **Symptom → How to confirm (commands) → Step-by-step fix → Rollback → Escalation**.
- **API:** for every endpoint the method + path, auth, parameters (table), a request and response example, error codes.

## Verification and proofreading
- **Run** the procedures from the document and check the result — test the description like code.
- Content review and language proofreading are **two separate passes** (content first).
- A review by someone without deep knowledge of the system catches the author's "obvious things". In a repeat review mark the changes.
- **Polish text before handing it in** → a language check: txt-polish-correctness (correctness), txt-polish-style (editing)
  or the persona Stefan (editor).

## Index of references
- Read `references/style-and-structure.md` when you plan the structure of a larger document (what goes at the start/end, glossary,
  navigation, formatting, traits of good documentation).
- Read `references/process.md` when you run writing as a process: gathering information, consulting developers,
  plan and milestones, review methods, proofreading, taking over someone else's documentation, post-mortem.
- Read `references/documentation-types.md` when you choose a page type (Diátaxis), write for developers
  (quick start, reference, error list), troubleshooting, FAQ or release notes.
- Read `references/maintenance-and-measurement.md` when you maintain a documentation site: reviews, links and examples in CI,
  gaps from tickets, style guide and Vale, metrics.
- Read `references/technical-content-and-seo.md` when you write an article, comparison or case study for a technical
  audience: funnel, SEO, distribution.
- Read `references/diagrams-and-presentations.md` when the document needs a diagram (Mermaid, C4, UML), an HTML page
  with an explanation or a presentation: choice of form, notation, readable layout, Mermaid pitfalls, accessibility, slides.

## Checklist
- [ ] I know the audience and chose the approach (descriptive/task-based).
- [ ] The most important things first; steps as lists, comparisons as tables.
- [ ] Terms and formatting consistent across the document.
- [ ] Code examples work (checked), data made up, no secrets.
- [ ] No `TBD` (or deliberately left and reported).
- [ ] A separate language proofreading pass (Polish text → txt-polish-*).
- [ ] Documentation changed in the same commit as the code.

Sources (described in our own words): the Transparent Data guide to the technical documentation of applications; "What is Technical
Documentation and Why it Matters"; testerzy.pl "Jak poprawnie tworzyć dokumentację"; Keep a Changelog.
