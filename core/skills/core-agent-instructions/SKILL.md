---
name: core-agent-instructions
description: Use when writing, trimming, auditing or splitting CLAUDE.md, AGENTS.md or .claude/rules — what earns a line, where it lives, the lint card, A/B check of a rule.
metadata:
  review: "2027-02-20"
  catalog: "Use when you create, shorten, review or refresh a project's agent-instruction files (CLAUDE.md, AGENTS.md, CLAUDE.local.md, .claude/rules/), the agent ignores rules in them, a monorepo needs module rules, several AI tools share one rule set or a rule's worth is in doubt — the inclusion test, where each kind of content lives, the instructions_lint card, refreshing from git history, A/B trials of a rule, module files with an index. Not for writing skills (core-skill-authoring), project lessons and the record (core-project-record) or a README and documentation for people (docs skill, pack-docs)."
  keywords: "CLAUDE.md puchnie, za długi CLAUDE.md, odchudzić CLAUDE.md, uporządkować plik instrukcji, agent ignoruje reguły, agent łamie zasady mimo reguły, co wpisać do CLAUDE.md, czy dodać regułę, nowa reguła w CLAUDE.md, przegląd CLAUDE.md, przegląd instrukcji agenta, nieaktualne wpisy, po refaktorze instrukcje nieaktualne, nieistniejący skrypt w instrukcjach, pisz czysty kod, wklejony tsconfig, zakaz na końcu pliku, monorepo, zasady pakietu, CLAUDE.md w module, zagnieżdżony CLAUDE.md, .claude/rules, paths, indeks modułów, AGENTS.md i CLAUDE.md, Codex i Claude Code, wspólne reguły dla kilku narzędzi AI, @AGENTS.md, dowiązanie symboliczne, kalibracja reguły, czy reguła działa, czy reguła coś zmienia, reguła zajmuje kontekst, A/B reguły, reguła z sąsiedniego repo, agent startuje w innym repo, globalne instrukcje, CLAUDE.local.md, instrukcje osobiste, pierwszy CLAUDE.md, /init, instructions_lint, bloated CLAUDE.md, trim CLAUDE.md, agent ignores rules, what to put in CLAUDE.md, stale instructions, AGENTS.md vs CLAUDE.md, module CLAUDE.md, monorepo rules, path-scoped rules, does this rule help, rule calibration, cross-repo rules, instruction file review"
---

# Agent instruction files — lean, placed right, checked

An instruction file is onboarding for an agent that already knows the language and the framework but not this
project's agreements. Every line is paid for in context by every session and every executor, and adherence falls as
the file grows: models use the middle of a long context worst (Liu et al., "Lost in the Middle").
Measured effect: an AGENTS.md cut median runtime by ~29% and output tokens by ~17% at comparable quality (Lulla et al.,
10 repos, 124 PRs); generic context files did not raise success and cost 20%+ more — repo overviews did not help,
non-standard practices did (Gloaguen et al.). So: few lines, each one something the agent could not guess.

## 1. Does it earn a line?
Add a line only when the agent **cannot get it** from its training, the framework docs, the README, lint/type/format
config or the code itself — and, ideally, only **after a recurring miss**: the same mistake twice, the same correction
typed again, a review remark the agent had no way to know.
- **Earns a line:** non-obvious local conventions, project pitfalls, workarounds for known dependency bugs, the exact
  build/test/lint commands, a pointer to a model file ("new endpoints follow `src/api/orders.ts`").
- **Does not:** framework documentation, README copies, rules a linter or config already enforces, directory trees,
  dependency lists, intentions ("write clean code") — rewrite those as behaviour visible in a diff or delete them.
- "We use React hooks" fails (visible in the code). "New code never imports from `legacy/`" passes (not inferable, cheap,
  checkable).

## 2. Where each kind of content lives
| Content | Home |
|---|---|
| true for the whole repo, every session | root `CLAUDE.md` (or `AGENTS.md`), strongest bans first |
| true for one part of the code | module `CLAUDE.md` or `.claude/rules/*.md` with `paths` |
| a procedure used now and then | a skill |
| a check that must never be skipped | a hook or a permission rule — the file is context, not enforcement |
| personal preferences | `CLAUDE.local.md` (gitignored) or `~/.claude/CLAUDE.md` |
| a pitfall from one incident | `docs/project/lessons.md` (core-project-record); propose a line when it repeats |
| reference material | `docs/project/…`, linked from the file |

One rule, one place. The file may still state a ban at the top ("never commit secrets"), but the hook enforces it.
- **Several AI tools:** `AGENTS.md` is the single source of truth; `CLAUDE.md` holds `@AGENTS.md` plus Claude-only lines.
  Claude Code reads `AGENTS.md` on its own only when no `CLAUDE.md` exists — check with `/context` or the
  "Project instructions" setting.
- **Agent started in another repo:** a session started in repo A does not load repo B's files, even when it edits B.
  Put what B needs (fork, target branch, `gh -R org/b`) in global instructions or B's README too, and enforce the critical
  part with a script or hook.
- Monorepo, module files, loading rules: `references/context-scaling.md` (how files load: section 4).

## 3. First draft
1. Start from `/init` or by hand: README, manifest scripts, lint/format/type/test config, one or two CI files, two
   levels of the tree, `git log --oneline -n 30` for the commit convention.
2. Every statement from a file, command or commit (core-grounding); what you could not find becomes a question to the human.
3. Order by leverage: hard bans → 3–6 commands → conventions with a model file → testing → commits/PRs → security.
   No mission, values or team introduction.
4. No code block longer than 1–2 lines (link the file), no definitions of general concepts.
5. Budget: under ~200 non-empty lines for the root file (Anthropic's guidance); a module file 10–40 lines. Notes meant
   only for humans go in HTML comments — Claude Code strips them before loading.

## 4. Review: the lint card
`python3 .claude/skills/core-agent-instructions/scripts/instructions_lint.py [files…] [--root DIR] [--json] [--warn N] [--error N] [--strict]`
- Exit 0 = no ERROR (with `--strict` a WARN also fails), 1 = an ERROR, 2 = bad call. `--root .` scans every
  `CLAUDE.md`, `AGENTS.md`, `CLAUDE.local.md` and `.claude/rules/*.md` (skips `node_modules`, `.git`, `dist`…).

| id | Measures | OK / WARN / ERROR |
|---|---|---|
| `length` | non-empty lines, HTML comments and rule frontmatter removed | ≤ 200 / ≤ 500 / > 500 (`--warn`, `--error`) |
| `blocks` | fenced blocks over 3 lines, mermaid excluded | 0 / 1–2 / ≥ 3 |
| `intents` | vague-aspiration phrases, PL and EN | 0 / 1–3 / ≥ 4 |
| `order` | first critical rule (never/always/must/do not) in the first third | ERROR if it appears only after line 200 or a file over 30 lines has no headings; WARN if it opens with an introduction heading |
| `imports` | `@path` imports | WARN for a missing file; reports length with imports; flags `~/` imports as needing approval |
| `stale` | backticked paths, `npm run x`, `make x` that do not exist | 0 / ≥ 1 (skips the `team-factory` block and lines that are prohibitions) |

`--root` adds `repo.main_file`, `repo.unindexed` (a nested file not mentioned in the root file — add it under
"Modules with their own CLAUDE.md") and `repo.duplicates` (a module line repeating a root line).
**Manual check (4 of 5): unneeded knowledge** — run the §1 test on every line.

Rules for the review:
- every finding as `file:line`; an intention becomes a checkable proposal grounded in a project signal (a lint rule,
  a model file), else a stack default marked [assumption];
- contradicting rules across files = an error;
- default is **report only**. Reordering and cuts happen with consent and never change what a rule says.

Output: a first line with the path and a one-sentence verdict; a table of the five checks (check, verdict, count);
findings (check, `file:line`, problem, proposal); the three actions with the highest gain.

## 5. Refresh after the code moved
1. `git log -1 --format=%h -- CLAUDE.md` → the last change of the file (LAST).
2. `git diff LAST..HEAD --stat -- package.json Makefile .github/ README.md <lint configs>` → what changed since.
3. Lint `stale` plus `python3 .claude/skills/core-grounding/scripts/grounding_check.py CLAUDE.md` for every path and command.
4. Mark each line KEEP / FIX / REMOVE / MISSING with its evidence `file:line`; show the list.
5. Edit point by point with consent — never a wholesale rewrite; the human's uncommitted edits count as KEEP.
6. After a major model upgrade, prune workarounds written for an older model's weaknesses.

## 6. Does a rule pay for itself?
A rule is a prompt change; test it like one, with repeated trials before and after:
1. Same task, 3–5 runs, each in a fresh session at the same repo state, **without** the rule. Note breaches of the
   convention, time, files read, iterations, cost.
2. Add the rule (1–3 sentences, in its right home), repeat the same runs.
3. No improvement, or the agent was already right → remove it. Change one variable at a time.
Changing the factory's own CLAUDE.md or personas is an agent-config change, evaluated per core-delivery-lifecycle.

## Anti-patterns
- the encyclopedia file; pasted docs, configs or README;
- architecture prose the agent could read in the code;
- the same rule in three files, or a module file copying the root;
- team agreements living only in someone's local memory;
- "read AGENTS.md" written as prose instead of an `@AGENTS.md` import;
- `@` imports used to "save" context — they load at start and count in full.

## Example
Input: `CLAUDE.md`, 280 non-empty lines; opens with "## About the project"; a 25-line pasted `.eslintrc`; "follow best
practices" and "keep the code clean"; the ban on raw SQL in handlers sits on line 240; it mentions `npm run e2e`, which
package.json no longer has.
Lint: `length` WARN (280), `blocks` WARN (1), `intents` WARN (2), `order` ERROR (first critical rule after line 200),
`stale` WARN (`npm run e2e`).
Report: "CLAUDE.md — the important ban is buried and a fifth of the file is pasted config." Top three actions:
1) move "never raw SQL in handlers — use `db/queries/`" to the top; 2) replace the `.eslintrc` paste with "lint rules:
`.eslintrc.cjs`"; 3) turn "best practices" into "each handler validates input with `schemas/` before the query", or
delete; drop `npm run e2e` (or ask what replaced it). Expected result ~190 lines. Nothing edited before the human agrees.

## Checklist
- [ ] each line passes "the agent could not know this", ideally after a repeated miss
- [ ] bans first, commands, conventions with a model file; no intro, no pasted config
- [ ] root under ~200 non-empty lines; module files 10–40 and indexed in the root
- [ ] must-not-skip rules backed by a hook or permission rule
- [ ] `instructions_lint.py` run, findings as `file:line`, report before any edit
- [ ] AGENTS.md as the source, CLAUDE.md imports it; no duplicated rules
- [ ] a new rule tested with 3–5 runs with and without it

## Sources
- Anthropic, Claude Code docs "How Claude remembers your project" (memory, imports, `.claude/rules`) and "Best
  practices" (code.claude.com, accessed 2026-10-10).
- Anthropic, "Define success criteria and build evaluations" (platform.claude.com, accessed 2026-10-20).
- Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", arXiv:2307.03172 (2023).
- Lulla et al., arXiv:2601.20404 (2026), effect of AGENTS.md on agent runtime and tokens.
- Gloaguen et al., arXiv:2602.11988 (2026), context files and agent success.
