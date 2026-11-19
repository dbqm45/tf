---
name: eng-codebase-mapping
description: Use for unfamiliar code and change impact assessment — entry points, layers from imports, hubs, cycles.
metadata:
  review: "2027-10-09"
  catalog: "Use when you must understand unfamiliar code or assess the impact of a change — entry points, layers from the import graph, central nodes and runtime vs lazy cycles (scripts/code_graph.py for Python, TS/JS, Java, C# and Go), territory from git history (changes over time, co-changes, contributors, bus factor, hotspots — scripts/git_territory.py), a module legend, a reading route for a newcomer, diff impact (1 step up and down, layers, risk), edge confidence, analysis of a single flow and researching code before a change (research.md). Not for assessing debt (eng-tech-debt-audit), choosing a refactoring (eng-refactor-planning) or designing boundaries (ddd-strategic-analysis)."
  keywords: "graf importów bez narzędzi, cykle importów, nieznane repo, mapa kodu, mapa repo, od czego zacząć czytać, punkty wejścia, graf zależności, historia gita, co się najczęściej zmienia, współzmiany, kto zmieniał, kogo zapytać, bus factor, ryzyko jednej osoby, hotspoty, analiza przepływu, jak działa ten feature, research przed zmianą, wpływ zmiany, import graph without tools, import cycles, unfamiliar repo, code map, repo map, where to start reading, entry points, dependency graph, git history, what changes most often, co-changes, who changed it, who to ask, single-person risk, hotspots, flow analysis, how this feature works, research before a change, change impact"
---

# Code map

Map first, then read. An agent that starts with random files uses up context and mistakes the periphery for the core.
You build the map from deterministic tools, and the language model only names and describes what the tools showed.

**A wide scan, then deepening.** A repo map is a wide, shallow scan from the CLI — a cheaper model can do it, because
the tools work outside the context. Deepening a single flow is a separate task with the map as input
(`references/flow-analysis.md`). Do not combine in one instruction looking for structure, choosing the important areas
and understanding behaviour — "read the whole repo" gives a flat summary without priorities. The directory tree
is a hypothesis: it does not show what changes, what breaks together or what is dead.

## Procedure
1. **Inventory:** the number of files and lines per directory/project, languages, frameworks. You treat the README and manifests as
   hints, not truth — the code is the source. With a large repo (> ~100 files in scope) agree the scope with the human.
1a. **Territory from history (a 12-month window)** — **run** `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --all`
   (`--json`, `--depth 3` when the result is too general, e.g. `src/backend`):
   - the top 10 directories and files by number of commits, without noise (lockfiles, snapshots, generated files, translations, `.env*`);
   - the same ranking per quarter — it tells a stable centre apart from a one-off campaign of changes;
   - co-changes: pairs of directories and files from the same commits (commits > 30 files skipped — a mass refactor
     glues unrelated files together); separately **hubs** changed together with many areas (configuration, translations, generated code);
   - files from the ranking that are not in `git ls-files` are marked — history speaks of the past;
   - hotspots: changes × non-empty lines (eng-tech-debt-audit).
1c. **Inventory and conventions without a model** (a large or foreign repo): `python3 .claude/skills/eng-codebase-mapping/scripts/repo_inventory.py
   <repo> [--budget-tokens N]` — languages, build files, exclusions (dependencies, build, generated code), modules
   and batches of files within a token budget for analysis in portions; `scripts/standards_scan.py <repo>` — tools
   from the configuration and conventions counted in the code (file names, tests, test and code idioms, error catching,
   logging, TODO) with a share, `file:line` examples and exceptions. These are data for a standard, not the standard.
   `scripts/schema_scan.py <repo>` — tables, columns, constraints and relations from SQL migrations (Flyway) and from JPA
   and EF Core entities with `file:line` (constraints = rule candidates). A report with evidence is checked by
   `scripts/recon_check.py <report.md> --repo <repo>`: the file and line exist, the quote matches the code (±2 lines),
   bullet points without evidence and without [assumption]/[unverified]/[question] are reported.
   `scripts/recon_scan.py <repo> --out <raw/>` — the scans above in one command, JSON results to files, a summary
   on screen (project reconstruction). `scripts/recon_cards.py <modules/> --repo <repo>` — module cards (JSON) as `modules/<module>.md` with evidence
   that `recon_check` can check; `--summary` gives a draft of the Modules section, `--rules` — `rules.md` from the cards' rules, `--into report.md` inserts the Modules section, `--prev <old cards>` when
   refreshing points to places in the documentation with markers of removed or changed rules.
   `scripts/recon_manifest.py write|diff <repo>` — batches and files with hashes; after changes it says which batches
   to analyse again; `scripts/recon_refresh.py prep|finish <repo>` — refreshing a reconstruction in two steps.
1b. **Contributors** (optional, for 3–5 risk zones): `git_territory.py --authors <path>` — without bots
   and commits whose author is an AI agent. This is a list of "whom to ask, which PRs to read", not owners: it does not
   say who still works here or whether those decisions are current. Knowledge in one person = a risk on the map: all
   areas at once are shown by `git_territory.py --bus-factor` (the fewest people with > 50% of commits, active in the 90 days before
   HEAD; "critical" = no one active, "high" = one person). In a one-person team it will come out as 1 everywhere — that is a fact,
   not a conclusion. On the map only a login or initials and the area, without judging people.
2. **A dependency graph from tools**, not from reading:
   - Nx: `nx graph --file=graph.json` (projects and dependencies), module boundaries from tags;
   - TS/JS: `madge --json` / `madge --circular`, dependency-cruiser (`--collapse`, `--focus`, `--reaches`, `--metrics`);
     Java: `jdeps`, ArchUnit, Maven/Gradle modules; other languages and the tools' blind spots: `references/wide-scan.md`.
   - Python, TS/JS, Java, C# and Go without these tools (not installed, no network): **run**
     `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo>` (`--impact <file>`, `--focus <path>`
     — imports across a module boundary, two `--focus` — the seam of a pair; `--json`) instead of
     writing your own scanner — it gives steps 3 and 5 and data for 4: scored entry points, edges between workspace
     packages, groups with direction, upstream pairs, hubs without barrels (re-exports), runtime cycles separately from those closed
     by lazy imports (in a function, `TYPE_CHECKING`, `import type`, `import()`); it splits a group with > 40% of the files
     one level lower by itself (`--group-depth N` turns this off). Take the numbers from the output; read the code to
     name the layers and check doubtful places (an entry point from the name alone, a cycle through `__init__`). C#: `using`
     links to every file of the namespace (coarse edges); Java: classes from the same package without an import
     are invisible; it recognises Java, C# and Go entries by `main` (`Program.cs`, `@SpringBootApplication`).
   - The graph omits runtime coupling (DI, flags, queues, webhooks, reflection, dynamic import, codegen) — write it
     into `unknowns`; a layer without a graph is "not covered by the tool", not "no connections".
3. **Entry points** — scoring candidates:
   a conventional name (`main.ts`, `app.config.ts`, `*.routes.ts`, `Application.java`) +3 · in the root or one level lower +1 ·
   the top 10% by number of outgoing imports +1 · the bottom 25% of incoming imports +1. In addition routes (routing), endpoints
   (controllers), queue handlers, scheduled jobs — `code_graph.py` lists them separately as entries from registries
   (Celery tasks, Django commands, the GraphQL schema, HTTP apps and routes, controllers and cron in Nest).
4. **Layers (3–10):** a group of files densely importing one another (import density inside > ~0.3) is a coherent
   layer; a group that is often imported and imports little itself is a foundation; dependencies should flow
   UI/API → services → data/utilities. An upstream arrow is a finding.
5. **Central nodes and cycles:** the files/classes with the largest number of connections (after filtering out `index.ts` barrels,
   types and constants) — here a change has the widest reach; always list import cycles, with their kind: runtime (breaks on
   import) or closed only by a lazy import or a type (coupling, not a loading error).
6. **Reading route (5–15 steps):** from the best entry point downwards along the graph (wider first, then down);
   2–5 tightly linked files are one step. Each step: what is here and why read it now.
7. **Module legend** for the areas relevant to change risk: role (core / supporting / peripheral) · depth
   (deep / shallow) · change profile (stable / volatile / seasonal) · reach (load-bearing / contained) · sensitivity.
   Every label with evidence; without evidence → `to verify` (details: `references/wide-scan.md`).
8. **Write-up:** `docs/project/04-architecture/codebase-map.md` with the date and the HEAD commit: (1) a TL;DR of 5–7 sentences + a layer
   diagram (Mermaid), (2) the terrain: core vs periphery, activity over time, (3) real connections (imports + co-changes
   + cycles, with the source), (4) 4–6 risk zones, each with one "why", (5) whom to ask (1–2 people per zone),
   (6) the first day: 5–8 files, (7) limitations: the time window, the method, what the map does NOT say. The working results of the scans
   go next to it (`codebase-map/territory.md`, `structure.md`); the map is a synthesis, not a copy of tables. Goal: after ~15 min a newcomer
   knows where things live, what is dangerous and where to start.

## Edge confidence
Every connection on the map has a label: **EXTRACTED** (from a tool/AST), **INFERRED** (from names, conventions,
DI configuration) or **UNCERTAIN**. You do not invent connections; you show uncertain ones rather than omit them.

## Assessing context tools (graph, index, code map)
A single better run proves nothing. You measure: accuracy, **repeatability** (good in each of N runs),
input tokens and the **usage rate** — whether the agent reaches for the tool at all (for the factory's skills and maps:
`hint_report.py`, "hinted but not used"). You provide the knowledge layer through a tool that returns a small subgraph with
sources, and do not paste it into the prompt (ai-evals, ai-rag).

## Change impact (diff)
1. Changed files: `git diff --name-only <base>...HEAD`.
2. **Map freshness in a monorepo:** `git diff --name-only <map-commit> HEAD -- <project-path>` — changes in other
   projects do not invalidate this project's map. In Nx it is faster: `nx show projects --affected`.
3. For each file: dependencies 1 step up (who uses it) and 1 step down (what it uses), the layers it touches.
4. Risk: the file's complexity, the number of edges between layers, the reach (how many projects/modules) → low/medium/high.
5. The result for the PR description: the list of affected modules, the risk, what to test (qa-regression).

## Researching code before a change (a step's `research.md`)
When a step's plan needs knowledge of existing code (patterns, data flow, touch points):
1. Read yourself the files the human pointed to and the project's lessons — they narrow what is worth researching.
2. Split the question into 2–4 areas; an unclear scope → 1–3 questions (scope, depth, emphasis). A narrow question → no questions.
3. Areas in parallel: a cheap implementer looks for files and patterns, a stronger one analyses many files; each returns with `file:line`.
4. Write-up in `docs/project/<step>/research.md` (the only file the research creates — it does not change code): date, commit,
   branch; Question · Summary · Findings (each with `file:line`) · Architectural conclusions · Historical context
   · Open questions. A follow-up question → a section "Follow-up research <date>" in the same file.
No `file:line` = no claim. Earlier reports and the map are a prior, not truth — you correct an outdated claim
explicitly. Internal research answers "what our code does", not "which library to choose"
(core-source-research). Deep analysis of a single flow: `references/flow-analysis.md`.

## Structural search
`rg` for text, ast-grep for structure (definitions, calls, signatures). Run the `ast-grep` binary: on
Linux `sg` is usually the change-group command (`/usr/bin/sg`), not ast-grep. Confirm every zero from ast-grep
with `rg` — a wrong pattern also gives zero. The table "which tool for which question": `references/wide-scan.md`.

## Example
**Situation:** "Where should I start reading the `shop` repo (Nx, Angular + NestJS)?"
**Result:** `nx graph` + `madge`; entry points `apps/api/src/main.ts` and `app.config.ts` (6 pts each), `app.routes.ts`
(4 pts); layers controller → `order.service.ts` → repository → `libs/db`; finding: `libs/db/src/audit.ts`
imports the service (upstream, a cycle — EXTRACTED); central node `order.service.ts` (23 connections); an edge through a
DI token — INFERRED. `git_territory.py`: `apps/api/src/orders` changed in every quarter (a stable centre),
the pair `orders` ↔ `libs/db/migrations` in 14 commits, the hub `libs/i18n`; two files from the ranking already deleted. Risk
zone: orders (load-bearing, volatile); whom to ask: 2 logins. A 7-step route, the map with a date and a commit.
More examples: `references/examples.md`.

## Checklist
- [ ] the graph from tools, not from guesses; scope agreed for a large repo
- [ ] territory from history: 12 months, quarters, co-changes without mass commits, file existence checked
- [ ] module legend with evidence for every label; runtime couplings in `unknowns`
- [ ] scored entry points, layers with the dependency direction, cycles listed with their kind (runtime / lazy)
- [ ] edges with a confidence label
- [ ] a reading route of 5–15 steps; the map with a date and a commit

## Sources
- 10xDevs course, ed. 3 (2026), module 4, lessons 2–3 (a project map from history and the graph, feature analysis) and their
  prompts; module 2, lesson 4 (researching code before a change) — training material (accessed 2026-10-09); described in our own words.
- dependency-cruiser 18.5.0 (`depcruise --help`, checked 2026-10-10): `--collapse`, `--focus`, `--focus-depth`,
  `--reaches`, `--metrics`, `--exclude`, `--do-not-follow`, `-T archi|mermaid|dot`; ast-grep 0.50.0; `/usr/bin/sg`
  in Ubuntu from the `login` package (checked 2026-10-10).
- Factory measurement (read 2026-10-18): a full map from `code_graph.py` vs the agent's own scanner on two repositories
  (TS ~22 thousand lines, Python ~860 thousand) — `docs/project/archive/research/20261018-code-graph.md`.

## Sources of inspiration
[Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) (entry point scoring, layer heuristics,
the reading route, diff impact with per-path freshness in a monorepo) and [graphify](https://github.com/Graphify-Labs/graphify)
(central nodes, cycles, edge confidence labels, "graph first, then grep") — described in our own words; instead of
their tools the factory uses `nx graph`, madge and jdeps.
