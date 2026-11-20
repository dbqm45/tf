---
name: eng-codebase-mapping
description: Use when entering an unfamiliar repo or assessing a change — import graph, entry points, cycles, history hotspots, who to ask, diff impact, research before a change.
metadata:
  review: "2027-10-09"
  catalog: "Use when you have to understand an unfamiliar repository or the reach of a change — a codebase map built from deterministic tools (nx graph, madge, dependency-cruiser, jdeps, or scripts/code_graph.py for Python, TS/JS, Java, C#, Go), scored entry points, layers, hubs and runtime vs lazy cycles, territory from git history (scripts/git_territory.py — hotspots, co-changes, contributors, bus factor), edge confidence labels, diff impact, research before a change (research.md), deepening one flow, evaluating context tools, and the reconstruction script suite. Not for assessing debt (eng-tech-debt-audit), choosing a refactoring (eng-refactor-planning) or designing boundaries (ddd-strategic-analysis)."
  keywords: "nieznane repo, nowe repo, od czego zacząć w repo, zrozumieć strukturę repo, mapa kodu, mapa repozytorium, graf importów, graf importów bez narzędzi, graf zależności, cykle importów, cykliczne zależności, huby, punkty wejścia, gdzie zaczyna się wykonanie, warstwy w kodzie, trasa czytania, co czytać najpierw, hotspoty, co zmienia się najczęściej, co zmienia się razem, współzmiany, kogo pytać o kod, bus factor, wpływ zmiany, wpływ diffu, ryzyko zmiany przed PR, czy mapa jest aktualna, research przed zmianą, zbadać kod przed zmianą, analiza przepływu, prześledzić przepływ, ocena narzędzi kontekstu, graf kodu MCP, rekonstrukcja projektu, unfamiliar repo, where to start, understand the codebase, codebase map, import graph, dependency graph, import cycles, circular dependencies, entry points, hotspots, co-change, who to ask, bus factor, change impact, diff impact, research before a change, flow analysis, code graph tool evaluation"
---

# Codebase map — tools find the structure, the model names it

Map first, then read. Deterministic tools (an import graph, git history) produce the structure and the numbers; the model only names
layers, describes roles and checks doubtful items in the code. A directory tree is a hypothesis, not evidence.
Keep two jobs apart: a **wide, shallow scan** of the whole repo (a cheaper model is fine) and **deepening one flow**
(`references/flow-analysis.md`). Never ask in one instruction to "find the structure, pick the important areas and explain the
behaviour" — that produces a flat summary of everything.

## Procedure — the map
1. **Inventory.** Files and lines per directory/project, languages, frameworks, manifests; README and manifests are hints, not facts.
   `python3 .claude/skills/eng-codebase-mapping/scripts/repo_inventory.py <repo>` (budget for reading: `--budget-tokens`).
   More than ~100 files in scope → agree the scope with the human first.
2. **Territory from history** (default window 12 months):
   `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --repo <repo> --all`.
   - Top directories/files by commits, without noise (lockfiles, snapshots, generated code, translations, `.env*`; more with `--exclude`).
   - `--by-quarter`: at the top in every quarter = **stable centre**; in one quarter = a **campaign** (check whether it finished).
   - `--cochange`: pairs and hubs; commits touching more than `--max-files` (30) files are skipped — mass changes glue unrelated files.
     A pair sharing ≥ 0.8 is a hidden agreement; a pair caused by regeneration is cheap — flag it. A hub (config, i18n, route registry)
     co-changes with many areas; the hub ranking is not the pair ranking. No co-change does not prove independence.
   - `--hotspots`: changes × non-empty lines. Files in the ranking that `git ls-files` no longer lists are marked removed and stay off the
     reading route.
   - Whom to ask: `--authors <path>` lists people active in an area (bots and AI-agent commits excluded) — a list of people to ask, not
     owners. `--bus-factor`: the fewest people covering > 50% of commits, active in the 90 days before HEAD (`--active-days`);
     "critical" = nobody active, "high" = one person. A solo team shows 1 everywhere — a fact, not a finding. Show login/initials and
     the area, never a judgement of people.
   - No git history (a zip export, a squashed import) → skip this step and say so under Limitations; never invent history.
   Reading the output: `references/wide-scan.md` §4.
3. **The import graph.** Use the project's tool if it has one: `nx graph --file=graph.json`, `madge --json` / `madge --circular`,
   dependency-cruiser (levers and pitfalls: `references/wide-scan.md` §2), jdeps. Otherwise
   `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo>` — do not write your own scanner. Take the numbers from the
   output; read code only to name layers and to check doubtful items (an entry point found by its name alone, a cycle through
   `__init__.py`). C#: edges are coarse, at namespace level; Java: same-package classes without an import are invisible.
   The graph misses runtime coupling (DI, flags, queues, webhooks, reflection, dynamic import, codegen) → write it into `unknowns`.
   A layer the tool did not see is "not covered by the tool", not "no connections". Blind spots per ecosystem: `references/wide-scan.md` §3.
4. **Entry points.** `code_graph.py` scores candidates with an illustrative heuristic (tune it per repo): a conventional name (`main`,
   `app`, `manage.py`, `urls.py`, `index`) +3, at the root or one level down +1, top 10% by outgoing imports +1, bottom 25% by incoming
   imports +1. It also reads registries: Celery tasks, Django management commands, the GraphQL schema, HTTP apps and routes, Nest
   controllers and cron jobs. Add routes, endpoints, queue handlers and scheduled jobs you find in configuration. A file with no
   incoming edge is "unreachable by static imports", not "dead code" until registries and dynamic loading are checked.
5. **Layers** (3–10). A group that imports densely inside itself (internal import density above roughly 0.3) is a layer candidate;
   imported often and importing little = a foundation. The intended direction is UI/API → services → data/utils; an arrow upstream is a
   finding. `code_graph.py` splits a group holding more than 40% of files one level down.
6. **Central nodes and cycles.** Highest connectivity after dropping barrels (re-export-only `index.*`/`__init__.py`), types and
   constants. List every cycle, typed **runtime** (module-level imports — can break on import) or **lazy/type-only** (closed by an import
   inside a function, under `TYPE_CHECKING` or `import type` — coupling only).
7. **Reading route.** 5–15 steps from the best entry point downwards, 2–5 tightly related files per step, each step says why now.
8. **Module legend and couplings.** Per module: role, depth, change profile, reach, sensitivity — each with evidence, otherwise
   `to verify`; couplings incoming/outgoing, contractual, runtime, co-change, each with its source or "the tool did not cover it"
   (`references/wide-scan.md` §5–6).
9. **Write the map** to `docs/project/04-architecture/codebase-map.md` with the date and the HEAD commit; working results in
   `codebase-map/territory.md` and `codebase-map/structure.md`. Sections: TL;DR in 5–7 sentences with a Mermaid layer diagram; terrain
   (core vs periphery); real connections with sources; 4–6 risk zones, each with a why; whom to ask (1–2 per zone); first day (5–8 files);
   Limitations (window, method, blind spots). Goal: a newcomer is oriented in about 15 minutes. It is a synthesis, not a dump of tables.

## Edge confidence
Every connection on the map carries a confidence label: **EXTRACTED** (read by a tool from imports/AST), **INFERRED** (from names,
conventions, DI configuration), **UNCERTAIN** (plausible, unchecked). Never invent an edge; show the uncertain ones instead of hiding them.

## Diff impact and map freshness
- Changed files: `git diff --name-only <base>...HEAD`. Is the map still valid for a project in a monorepo:
  `git diff --name-only <map-commit> HEAD -- <path>` or `nx show projects --affected`.
- Per changed file one step up (who uses it) and one step down (what it uses), and the layers touched:
  `code_graph.py <repo> --impact <file>`; dependency-cruiser `--affected <revision>`.
- Risk low / medium / high from complexity, cross-layer edges and reach (with their confidence labels). Output: affected modules,
  risk, what to test (qa-regression).

## Research before a change
1. Read the files the human pointed to and `docs/project/lessons.md` first. Earlier maps and reports are priors, not truth.
2. Split the question into 2–4 areas; ask 1–3 scoping questions only if the scope is unclear.
3. Investigate the areas in parallel, read-only: a cheaper worker finds the files, a stronger one analyses many of them.
   Every claim gets `file:line`.
4. Write `docs/project/<step>/research.md` with: Question, Summary, Findings (file:line), Architectural conclusions, Historical context,
   Open questions. A follow-up goes into a section "Follow-up research <date>". It is the only file produced — no code changes.
Choosing a library or an external solution is not code research: core-source-research.

## Deepening one flow
One flow, the current state only, the map as a prior (or the human's explicit consent to go without one): `references/flow-analysis.md`.

## Evaluating context tools (code graph, semantic index, MCP)
One good run proves nothing. Measure on the same tasks with and without the tool: accuracy; repeatability over N runs; input tokens and
cost; the usage rate — does the agent reach for the tool at all (the factory's `hint_report.py` shows "hinted but not used"). Deliver
knowledge through a tool that returns a small, sourced subgraph, not pasted into the prompt. Method: ai-evals; retrieval: ai-rag.

## Scripts
All under `.claude/skills/eng-codebase-mapping/scripts/`, standard library only, read-only on the repo, no network. One-line catalogue
and the reconstruction chain (inventory → scan → cards → check → export/refresh): `references/scripts.md`; flags: each script's `--help`.

## Example
Input: "A Django + TypeScript repo, no madge, no network. Map it."

Result (`docs/project/04-architecture/codebase-map.md`, 2026-11-20, HEAD `9c41e7a`):
- `repo_inventory.py`: 1,140 files, Python 61%, TS 34%; scope agreed: `backend/` and `web/src/`.
- `git_territory.py --all`: stable centre `backend/orders/` (top in 4/4 quarters); campaign `web/src/checkout/` (Q2 only, finished);
  pair `backend/orders/models.py` ↔ `web/src/api/generated.ts` share 0.92 — regeneration, cheap; hub `backend/settings/base.py`.
- `code_graph.py`: entry points `manage.py` (score 5), `backend/config/celery.py` (registry: 14 tasks), `web/src/main.tsx` (5);
  runtime cycle `orders/services.py → billing/hooks.py → orders/services.py`; a lazy cycle closed by a `TYPE_CHECKING` import;
  barrel `web/src/components/index.ts` excluded from hubs.
- Unknowns: signals in `orders/apps.py` connect billing at runtime — INFERRED, not in the graph.
- Risk zones: `orders/services.py` (hotspot #1, runtime cycle), `billing/hooks.py` (bus factor: one person). First day: 6 files.
More cases (diff impact, co-change reading, a repo without history): `references/examples.md`.

## Sources
- git documentation: `git-log`, `git-diff`, `git-ls-files` (git-scm.com/docs, accessed 2026-10-10).
- Nx documentation, "nx graph" and "nx show projects --affected" (nx.dev, accessed 2026-10-10).
- dependency-cruiser documentation, CLI options (github.com/sverweij/dependency-cruiser, 18.5.0, accessed 2026-10-10).
- madge README (github.com/pahen/madge, accessed 2026-10-10); ast-grep CLI reference (ast-grep.github.io, accessed 2026-10-10).
- Sources of inspiration: the open-source code-knowledge-graph projects Understand-Anything and graphify (GitHub) — scored entry points,
  confidence-labelled edges [unverified: repository owners and access dates].
