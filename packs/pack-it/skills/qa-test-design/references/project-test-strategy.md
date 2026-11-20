# A risk-driven test strategy for a whole project

For a project that has run for a while with no tests, or with tests only where they were easy to write (helpers, formatters).
The goal is not coverage; it is protection against the failures that would hurt users or the business, introduced in phases.
The result is one document, `docs/project/05-plan/test-strategy.md`, written from `templates/test-strategy.md`
(its headings and fixed words are in Polish and stay as they are). The document plans; it contains no test code and no CI YAML.

## 1. When to use it
- Use: "the project is two years old, almost no tests, where do we start", "we need a strategy, not a plan for one change".
- Do not use for one feature or one change: that is a test plan (SKILL.md §5, `references/test-strategy-and-plan.md`).
- The approach follows risk-based testing as described in the ISTQB Foundation syllabus: identify product risks, assess
  them by likelihood and impact, and let the assessment drive the techniques, levels and order of work.

## 2. Step 1 — inputs and the test-base profile
Read what exists, and give every fact in the document a source (a document, a commit, the interview answer):
requirements (`docs/project/03-requirements/`), the roadmap or project plan, closed changes and the review record, the stack
and its test runner, `CLAUDE.md`.
Classify the existing test base with one of three words used by the template:
- `brak` — no tests that run;
- `rzadki` — some tests, but they do not protect the main flows (or are mostly on trivial code);
- `znaczący` — a suite that already guards the main flows; the strategy then fills gaps instead of starting over.
Write one sentence of justification (e.g. "12 tests, all in `src/utils/`, none on checkout").

## 3. Step 2 — where the code changes (git history)
Frequently changed code is where regressions appear. Count commits per directory in a recent window (e.g. 30 days):

```bash
git log --since=30.days --name-only --pretty=format: -- src | grep -v '^$' | cut -d/ -f1-3 | sort | uniq -c | sort -rn | head
```

- Count only hand-written code: skip lockfiles, generated clients, migrations snapshots, vendored code.
- Show the human the window and the directories you counted, and let them accept or change the scope.
- Fewer than about 5 commits in the window → skip this step and write "pominięte (< 5 commitów)" in the document.

## 4. Step 3 — a short interview
Questions to the human, **one at a time**; after three skipped questions stop and continue with what you have.
The template labels the answers W1–W5:
- **W1** — which failure would hurt most: what are you most afraid of breaking?
- **W2** — what has broken before (incidents, angry customers, hotfixes)?
- **W3** — which flows bring money or carry legal obligations?
- **W4** — what is about to change (roadmap, migrations, a new integration)?
- **W5** — what is already checked another way (manual QA, monitoring, a vendor's guarantees)?

## 5. Step 4 — the risk map
- A risk is a **failure scenario seen by a user or the business** ("an invoice is sent with the wrong VAT rate"), not a module
  name ("billing").
- Rate impact and probability (high / medium / low each). Keep the map short enough to act on — roughly 5–7 rows.
- High impact with low probability usually becomes **monitoring** (an alert, a dashboard) rather than a test; say so.
- The source column cites the evidence (W2 answer, incident note, commit count), not `file:line`.
- For anything with login, payments or untrusted input, also look at abuse: access to someone else's resource, untrusted input
  reaching a query or a template, data leaking in responses or logs, resource abuse (unbounded uploads, request floods).
  Deeper analysis: arch-threat-modeling.

## 6. Step 5 — the response to each risk
One row per risk:
- **what will prove protection** — an observable result ("an invoice with a reduced rate shows 8% and the right total");
- **what to settle in the code first** — the context the tester still lacks (where the rate is chosen);
- **the cheapest layer** that can prove it — a hypothesis to confirm when the phase starts (unit for the rate rule,
  integration for the PDF);
- **the anti-pattern to avoid** — e.g. an e2e test for every rate, a test that recomputes the rate with the production formula.
The template also has a column for an assumption worth challenging; fill it only when there is one.

## 7. Step 6 — review before writing
Before the document is saved, go through the map once more:
- is each risk backed by evidence (a defect, an incident, a real change), or is it speculation?
- did an example from the interview leak into every row (anchoring on one story)?
- does the plan protect against real regressions, or does it just raise coverage numbers?
Remove or rephrase what fails, and note it under "Wyniki kontroli".

## 8. Step 7 — rollout phases and their states
- 3–5 phases, each named after the protection it proves ("phase 1 — wrong totals cannot reach an invoice"), each tied to risks
  and the kinds of tests it adds.
- A phase's state is derived from what is on disk (the change folder for that phase and its files), in this fixed order:
  `nie rozpoczęta` → `otwarta` → `zbadana` → `zaplanowana` → `w realizacji` → `zakończona`.
- Each phase is delivered as an ordinary change through core-delivery-lifecycle.

## 9. Step 8 — quality gates, recipes, exclusions, freshness
- **Quality gates** — each is either already wired (pre-commit, CI job) or tied to the phase that will introduce it
  (eng-local-quality-gates, ops-ci-cd).
- **Recipes** ("Przepisy") — how a unit, integration and e2e test is written in this project. Until a phase delivers one,
  the line reads `TBD — faza N (ochrona przed <zachowanie>)`. After each phase, fill it in and copy the short form into `CLAUDE.md`,
  so agents follow it.
- **What we knowingly do not test** — a short list (about five items) with the reason and when to reassess
  (e.g. "admin CSV export — used twice a year, manual check; reassess when customers get access").
- **Freshness** — the review date and the triggers for a new review: a new integration, a serious production defect,
  a phase finished, a major framework upgrade.

## 10. Example
A two-year-old SaaS invoicing app, 12 tests in `src/utils/`.
- Profile: `rzadki` — "12 tests, all on formatters; nothing on invoice totals or payments".
- Git (30 days): `src/billing` 41, `src/invoices/pdf` 17, `src/auth` 6 commits.
- W1: "wrong amounts on invoices". W2: "last quarter a VAT change broke reduced rates".
- Risk map (top 3): wrong VAT total on an invoice (high/high, W1+W2); a customer sees another customer's invoice (high/low → test + monitoring);
  a failed payment marked as paid (high/medium).
- Phases: 1 — totals and VAT (unit, table-driven); 2 — tenant isolation of the invoice API (integration, two seeded tenants);
  3 — payment webhooks (contract + integration).
- Not testing: PDF layout pixel-perfectness (visual review per release), admin export.
