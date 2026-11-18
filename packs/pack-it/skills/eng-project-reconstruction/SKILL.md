---
name: eng-project-reconstruction
description: Use when you must reconstruct from the code alone what a project is — stack, modules, domains, rules, evidence.
metadata:
  review: "2027-04-23"
  catalog: "Use when you must reconstruct a project description from the repository alone (large, old, many languages, no documentation): the stack, modules, domains and glossary, requirements from tests and validation, business rules, standards actually applied in the code, risks, questions for people — a report in docs/project/00-reconstruction/ with file:line evidence for every claim, CLAUDE.md and REVIEW.md drafts from the standards, incremental refresh after changes (a manifest with hashes), an HTML version for reading. First scripts without a model (an inventory and batches within a budget, a graph, git history, standards, the database schema), then module cards with a cheaper model, synthesis with a stronger one, evidence checking with a script. Not for describing the architecture before a refactor with an assessment and a roadmap (eng-legacy-dossier), the map and change impact alone (eng-codebase-mapping), debt (eng-tech-debt-audit) or a full audit with security (eng-code-audit)."
  keywords: "rekonstrukcja projektu, odtworzyć z kodu, z samego kodu, czym jest ten projekt, przejąłem repozytorium, przejęte repo, duże repozytorium, bez dokumentacji, raport o projekcie, opis projektu, stack projektu, domeny z kodu, wymagania z kodu, wymagania z testów, reguły biznesowe z kodu, standardy z kodu, konwencje zespołu, których zespół przestrzega, agent ma pisać tak samo, CLAUDE.md z kodu, REVIEW.md, słownik domeny z kodu, odświeżyć raport, zaktualizować raport, zmieniło się kilkadziesiąt plików, maister, automat ma znać projekt, kontekst dla agenta, raport w przeglądarce, raport HTML, pokazać raport zarządowi, project reconstruction, reconstruct from code, from the code alone, what this project is, I took over a repository, inherited repo, large repository, no documentation, project report, project description, project stack, domains from code, requirements from code, requirements from tests, business rules from code, standards from code, team conventions, which the team follows, the agent should write the same way, CLAUDE.md from code, domain glossary from code, refresh the report, update the report, dozens of files changed, the automaton should know the project, context for the agent, report in the browser, HTML report, show the report to the board"
---

# Reconstructing a project from code

Goal: from the repository alone a report is produced that a human reads in a quarter of an hour and an agent (e.g. a story automaton) reads
on every change. The code is the source of truth, every claim has `file:line` evidence or the marker
[assumption] / [unverified] / [question] (core-grounding). You change nothing in the code.

**Cheaper than "read the repo":** the model never reads the whole repository. First the scripts compute (zero tokens),
the model gets summaries and batches within a budget; the cheapest sufficient model per step (core-cost-control).
The scripts are in `.claude/skills/eng-codebase-mapping/scripts/`; below I give only the names.

## Procedure
0. **Scope and budget.** The HEAD commit, the scope (everything or directories), a USD budget from the human. `repo_inventory.py
   <repo>` gives tokens and batches — show the cost estimate (batches × the card model's price list) before the start. A run plan
   with fields to tick off in `docs/project/00-reconstruction/plan.md` — after a break you resume from it.
1. **An inventory without a model, with one command:** `recon_scan.py <repo> --out docs/project/00-reconstruction/raw` —
   the inventory and batches, the graph, the history, standards with idioms, the database schema to `raw/*.json`, a summary on screen.
   You read the summary; for details you go to the specific JSON file, you do not run the scans separately.
2. **Module cards** — always workers on the cheapest model (Haiku), also in a small repository: a batch
   from `raw/inventory.json` = one task, in parallel (join small batches a few at a time into one task). The main model
   does not read the batches' source files; the worker writes the card to a file and answers with one line. You launch all
   the workers in one message, in the foreground (no background work), and wait for their answers —
   you do not poll the `modules/` directory in a loop (every check is a turn with the full context). A prompt with a fixed
   beginning (`references/prompt-cards.md`) and a variable ending (the list of the batch's files) — the shared prefix hits
   the cache. The result: JSON per `references/module-card.json` in `modules/<module>.json`.
   The worker itself runs its card through `recon_cards.py` (card → `modules/<module>.md`, evidence relative to
   the batch corrected) and `recon_check.py` and fixes bad evidence. After all the cards `recon_check.py modules/ --repo
   <repo>`; you return a card with bad evidence to the worker once (you do not fix it yourself), then escalation to a stronger model.
3. **Domains and glossary** (a stronger model, input: the cards + the graph): subdomains, contexts, a glossary term → `file:line`,
   name mismatches code ↔ business (ddd-legacy-modernization, ddd-strategic-analysis).
4. **Requirements and rules:** `recon_cards.py modules/ --repo <repo> --rules` assembles `rules.md` from the cards' rules without
   a model; cross-cutting rules and constraints from `schema.json` you add under the heading `## Cross-cutting rules`
   (reassembling keeps it). Requirements from tests (names, assertions),
   validation and endpoints from the cards; each
   with a confidence: `test` (there is a test) / `code` (code only) / `to confirm`. A mapping (error → HTTP code, a list of domain
   errors, enum values) you write out in full, including the default case and the success code.
5. **Standards:** a signal from `standards_scan` (share, examples, exceptions) → a rule after looking at the examples. A file per
   area in `standards/` + `standards/INDEX.md`. A share < 70% is not a standard, only "mixed" with exceptions.
   The signals `test idioms` and `code idioms` you assess within the place they concern (the tests of a given layer,
   controllers, aggregates), not against all files. The test standard gives, with a `file:line` example: the kind of test
   per layer (e.g. a web test, a repository test, an integration test), the test double library, the case structure (subtests,
   a table, parameters), test data (builders, fixtures). The code standard: idioms of signatures, encapsulation and controllers,
   lifetimes in the DI registration. The `layout` signal (packages by feature or by layer) gives the standard "where to put new
   code" with examples of directories and exceptions.
6. **The report** `report.md` per `references/report.md`; the Modules section is inserted by `recon_cards.py modules/ --repo <repo>
   --into report.md` (you do not rewrite it; module details are in `modules/*.md`) + the drafts `CLAUDE.draft.md` and `REVIEW.draft.md`
   (`references/sketches.md`) — for a human to approve, you do not write them into `CLAUDE.md` yourself. After approval
   `python3 .claude/skills/core-git-workflow/scripts/ai_review.py review-md` moves the draft to `REVIEW.md` (the rules of
   PR review by AI in CI: `ai_review.py install`).
7. **Control:** `recon_check.py docs/project/00-reconstruction --repo <repo> --final` — zero bad evidence,
   all sections, claims without evidence marked, the stack table with the required rows (with versions, CI, tests
   and configuration; the CI row points to the pipeline file, if there is one in the repo), every module from the cards listed
   in the Modules section and with a current `modules/<module>.md`. A report of the run's cost (core-cost-control), then
   `recon_manifest.py write <repo> --out docs/project/00-reconstruction/manifest.json --budget-tokens N --cost-usd X`.
   **JSON export** for tools (e.g. requirements control as the "current state"): `recon_export.py
   docs/project/00-reconstruction --repo <repo>` → `reconstruction.json` — rules, requirements and the glossary from the same
   files, evidence split into file and lines with `verified`, confidence, state (evidence / assumption / question), modules from the cards,
   the commit from the manifest and a stable item identifier from the content (tracking between refreshes). Without a model.
8. **A reading version (optional):** one HTML page from `report.md` (a table of contents, tables, evidence as text).
   When the session has the Artifact tool — a private page, the human shares it; without it a
   `report.html` file next to it. Markdown remains the source of truth; the page is a view, after a refresh you generate it anew.

## Result
`docs/project/00-reconstruction/`: `plan.md`, `raw/`, `modules/*.json`, `domain.md`, `requirements.md`, `rules.md`,
`standards/` with `INDEX.md`, `report.md`, `CLAUDE.draft.md`, `REVIEW.draft.md`, `manifest.json`
(the base commit, batches and files with a sha256 hash, the batch budget, the date, the cost), `reconstruction.json` (the export, format
`reconstruction-export.schema.json` next to the script — a copy of `reconstruction.schema.json` from the pdi contract;
`recon_refresh.py finish` refreshes it together with the manifest),
optionally `report.html`.

## Incremental refresh
Goal: a few turns of the main model. The first command is `prep` (without a preliminary `git status` and `ls`); you do not read
the batches' code yourself, you do not do scans and copies manually.
1. `recon_refresh.py prep <repo>`: a diff against the manifest and the previous versions of files from git. Changes only in comments
   and blank lines get no tasks; the line numbers of evidence in the cards and documents are recalculated. In addition a copy
   of the cards to `raw/cards-prev/`, tasks `raw/refresh/<card>.md` with the diff of the changed files, a list of files without a card.
   With no tasks `prep` itself runs `finish` — you go to step 4. More than half of the files changed → a full run.
2. Workers (Haiku) in one message, in the foreground; each gets one sentence: "Carry out the task
   from <path>". The worker updates the old card (only the changed files) and checks the evidence itself.
3. `recon_refresh.py finish <repo>`: cards → `.md`, `rules.md`, the Modules section, the refresh date and commit in the report
   header, changed card rules (old → new), places to check with the full line content (an old marker, evidence
   in a changed code line, a description similar to a changed rule; also in `raw/refresh/STALE.md`), evidence shifted by
   a code change corrected automatically, `recon_check --final`, and when it passes — a new manifest.
4. Fixes from the `finish` printout in one message, without reading files (unless a line from the list is not enough): lines
   marked "from card" you fix in `modules/<card>.json`, the others you write (Write) to `raw/refresh/fixes.md`
   as `@@ file:line` blocks with the new line content (an empty block deletes the line) and in the same message you run
   `recon_refresh.py apply <repo>` — it replaces the lines and immediately runs `finish`. No heredoc and no `sed -i`. The description
   of a removed rule you replace with a sentence about the current state ("… is no longer checked"), you do not delete it; an empty block
   only for repetitions. A summary that gives only part of a changed rule (e.g. the lower bound without the new
   upper one) you complete with the current state. You leave a place when it describes the current state in full. In addition requirements from
   the changed tests.
   The control passed → you finish.
5. The final answer: up to 5 lines — what changed in the description, the control result.

## Rules
- **The main model's context is expensive:** every turn reads it anew. Full results stay in files, the model reads
  summaries and cards; you write files with one write, you run scripts with one command. You open source code
  only to check a specific piece of evidence (a fragment of a file, not the whole file).
- **Evidence or a marker** — no exceptions; the quote with the evidence must match the code (`recon_check` checks it).
- **What is not visible does not exist in the report:** DI, reflection, queues, HTTP calls between services, external
  configuration → "Not checked" and questions for people.
- **No network and no running of the repository's code**; you do not quote secrets from files (core-agent-security).
- **The budget is a STOP:** after the batch that exceeds it, you stop with a partial report and a plan for the further batches.

## Example
A repo of 400 thousand lines (Java + Go, 2012). `repo_inventory --budget-tokens 60000` → 38 batches, ~2.2 million tokens; the estimate
given to the human, approval for 6 USD. The step 1 scripts in a few minutes; 38 cards on Haiku in parallel; 3 cards came back after
`recon_check` (a wrong quote), one escalated. The standard "errors through domain exceptions" — 81% of service classes, exceptions
in `legacy/` → an entry with exceptions. The report: 14 rules with a test, 9 "to confirm", 6 questions; a `REVIEW.md` draft with 5 rules.

## Sources
- Claude Code — subagents, prompt caching, cost: the code.claude.com and platform.claude.com documentation.
- The evidence and marker rule: core-grounding; cost and model choice: core-cost-control.
