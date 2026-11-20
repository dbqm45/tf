---
name: eng-domain-agents
description: Use when a monorepo needs one agent and AGENTS.md per domain — domains detected from Nx tags, boundaries, aliases and imports.
metadata:
  review: "2027-05-20"
  visibility: name
  catalog: "Use when a monorepo should get one agent per domain plus a dispatcher — the domain layout is DETECTED by scripts/domain_scan.py (Nx projects and tags, module-boundary rules, tsconfig path aliases, real cross-domain imports, CODEOWNERS, routes, generated code, flags) and shown with evidence, never guessed; then a per-domain AGENTS.md (with CLAUDE.md = @AGENTS.md), a project pack with domain personas, a dispatcher persona and a routing skill, and a drift check for CI. Not for writing one CLAUDE.md (core-agent-instructions), mapping a codebase in general (eng-codebase-mapping) or discovering DDD bounded contexts (ddd-strategic-analysis, ddd-context-mapping)."
  keywords: "agenci domenowi, agent na domenę, agent dla każdej domeny, AGENTS.md w każdej domenie, monorepo nx, podział na domeny, dyspozytor domen, granice domen, agenci per moduł, dyspozytor agentów, domain agents, agent per domain, per-domain AGENTS.md, nx monorepo domains, domain dispatcher, module boundaries, enforce-module-boundaries, one agent per domain, domains.yaml"
---

# Domain agents for a monorepo

One agent per domain, each limited to its directory, plus a dispatcher that assigns tasks. The expensive mistake is a wrong
domain map, so a script **detects** it from facts and shows the evidence; the model writes only what facts cannot give
(a one-sentence scope) and marks it `[to confirm]`.

Script: `python3 .claude/skills/eng-domain-agents/scripts/domain_scan.py` (`py` on Windows). Standard library only, no network, paths with `/`.
Run it, do not read it. It writes only the files listed by `plan`.

## Procedure
1. **Scan:** `domain_scan.py scan` (`--json` for the full facts). It lists candidate layouts with a score and evidence
   (Nx `project.json` and tags, `@nx/enforce-module-boundaries` rules, tsconfig `paths`, actual imports between domains,
   CODEOWNERS, routes, generated dirs, flag dirs). Exit 0: one layout clearly wins. Exit 1: ambiguous or no Nx (low confidence). Exit 2: call error.
2. **Exit 1: ask the human ONE question** listing the candidates with their evidence ("Which of these is the domain layout? `domains/*` (billing, catalog, shipping) or `libs/*` ...?"),
   with your recommendation. Write the answer to `.tf/config/domains.yaml` and scan again (exit 0, `source: config`):
   ```yaml
   layout: {glob: "domains/*"}          # directories that are domains
   domains:                              # optional: facts the code cannot give
     billing: {scope: "Invoices and payments.", owner: "team-billing", notes: ""}
   exclude: [shared]
   ```
3. **Plan:** `domain_scan.py plan --pack-dir tools/tf-pack --project-id <id>`; show the file list to the human
   (`new`, `changed`, `unchanged`, `kept` = edited by a human). Mention imports outside the allowed set: they are findings for the human, not for you to fix.
4. **Write:** `domain_scan.py write ...` (same arguments). Generated: `<domain root>/AGENTS.md`, `<domain root>/CLAUDE.md` (the single line `@AGENTS.md`, only when absent), and in `<pack-dir>/pack-<id>/`: `pack.yaml`, `personas/<domain>.yaml`, the dispatcher `personas/<id>.yaml`, the skill `<id>-domain-routing` with its evals, `README.md`.
   A file a human edited is never overwritten: the new version goes to `<file>.tf-new`. A `CLAUDE.md` without the import is reported, not changed.
5. **Fill the scope lines:** replace each `TODO(human): one sentence` in the AGENTS.md files only from evidence (README, routes, menu labels, project descriptions) and add `[to confirm]`. No evidence: leave the TODO. Do not invent rules; the inclusion test of core-agent-instructions applies (a line that corrects a recurring mistake or states a fact the agent cannot infer).
6. **Install the pack:** `python3 .tf/factory/update.py --pack-dir <pack-dir> --add pack-<id>` (`py` on Windows), then `python3 .tf/factory/build.py check`.
   Agents appear as `<domain>-<role>` (role `frontend` for Angular/React/Next, otherwise `backend`) and the dispatcher as `<id>`.
7. **Pilot:** one real task through `claude --agent <id>` (a one-domain task, then a two-domain one). Check that the dispatcher confirms the domain with `grep`, passes the first result to the second agent, and stops at a new cross-domain import.
8. **Keep current:** after structural changes (new domain, new boundary rule, new generate target) run `domain_scan.py check ...` (exit 1 = drift: names the new or removed domain and the changed part, e.g. `boundaries`, `commands`). In CI the same command guards the generated files.

## What the output contains
- Per domain: root, Nx projects and tags, entrypoints (`@org/<d>`, `@org/<d>/shared`), allowed imports (tags from the rules, domains they resolve to, the `allow` list), actual imports with counts, imports outside the allowed set, test/lint/single-file/generate commands, owners, docs, routes, generated and flag locations.
- Boundary checks work at domain level (an approximation of the tag rules). Without boundary rules the scan only lists actual imports.
- Domain names become agent names: lowercase letters, digits, hyphens. Check that a domain name does not collide with an existing persona.

## Example
Repo with `domains/{billing,catalog,shipping}`, tags `scope:<d>`, rules in `eslint.config.mjs`, aliases in `tsconfig.base.json`:
`scan` prints `Layout: dir-per-project  glob: domains/*  confidence: high`, and for billing `OUTSIDE boundaries: @acme/shipping`.
`write` creates `domains/billing/AGENTS.md` (Boundaries, Rules, Commands), `domains/billing/CLAUDE.md` (`@AGENTS.md`) and `tools/tf-pack/pack-acme/` with agents `billing-frontend`, `catalog-frontend`, `shipping-frontend` and the dispatcher `acme`.

## Boundaries
- Domains here are directories of a codebase. Discovering business bounded contexts is ddd-strategic-analysis and ddd-context-mapping.
- Changing existing boundary rules or `allow` entries is a human decision; this skill reports, it does not edit `eslint.config.*`.
- MCP calls (Jira, Figma) in the generated personas go through the `mcp-runner` agent; this skill makes none.
