---
name: core-agent-instructions
description: Use when writing and reviewing CLAUDE.md or AGENTS.md — the inclusion test, a check card, modules.
metadata:
  review: "2027-10-10"
  catalog: "Use when the project's agent instructions file is being created, swells, goes stale or does not work (CLAUDE.md, AGENTS.md, CLAUDE.local.md, .claude/rules/) — the rule inclusion test, where to keep what (a rule, a skill, a hook, memory), a draft from inspecting the repo, a five-check card with a script, an update from git history, A/B rule calibration, a ladder of files in modules with an index in the root, AGENTS.md next to CLAUDE.md. Not for writing skills (core-skill-authoring), project lessons and the record (core-project-record) or a README and documentation for people (the documentation skill, pack-docs)."
  keywords: "CLAUDE.md, AGENTS.md, CLAUDE.local.md, plik instrukcji agenta, reguły dla agenta, reguły AI, zasady dla agenta, cursor rules, .claude/rules, /init, CLAUDE.md za długi, CLAUDE.md puchnie, agent ignoruje reguły, agent łamie konwencję, porządki w CLAUDE.md, przegląd reguł, onboarding agenta, monorepo CLAUDE.md, CLAUDE.md w module, reguły per katalog, AGENTS.md i CLAUDE.md razem, Codex i Claude Code, Copilot, Cursor, kilka narzędzi AI, wspólne reguły agentów, reguły się rozjechały, czy reguła działa, nieaktualne wpisy w CLAUDE.md, refaktor a CLAUDE.md, agent instructions file, rules for the agent, CLAUDE.md too long, agent ignores the rules, review the rules, rules per directory, several AI tools, does the rule work, outdated entries, czy reguła coś zmienia, reguła zajmuje kontekst, kalibracja reguły, test A/B reguły, does the rule change anything, the rule takes up context"
---

# Instructions for agents in a project (CLAUDE.md, AGENTS.md, rules)

An instructions file is the onboarding of an agent that knows the language and the framework, but not your local agreements. Every line
costs context in every session and for every executor, and the rules from a long file are followed more weakly.
The skill gives criteria for what to write, where to keep it, how to review the file and how to check that a rule works.
The architecture of files in a big repo (modules, an index, many repositories): `references/context-scaling.md`.

## 1. The inclusion test (before adding every line)
"Would the agent know this without this file — from training data, the framework's documentation, the README, the linter
configuration or from the code itself?" Yes → do not add it (at most a link). No → add it.
- **Belong:** non-obvious conventions (the shape of an API error, file naming, allowed imports), the project's pitfalls,
  workarounds resulting from history or a dependency bug, the build/test/lint commands, pointing to a model file
  (`src/users/user.service.ts` instead of a pasted example).
- **Do not belong:** framework documentation, README content, rules already enforced by configuration (`strict` in tsconfig),
  a description of the directory structure and lists of dependencies (the agent reads them from the repo), intentions ("write clean code") — replace them with
  behaviour checkable in the diff or remove them.
- A rule without a recurring agent mistake does not go into the file "just in case". Signals that it needs adding: the same agent
  mistake a second time, the same correction typed in the next session, a code review remark the agent could not have known.

## 2. Where to keep what
| Content | Place |
|---|---|
| applies always, across the whole repo | the main `CLAUDE.md` / `AGENTS.md`, the most important bans on top |
| concerns a part of the code | a `CLAUDE.md` in that part's directory or a `.claude/rules/*.md` rule with a `paths` field |
| a procedure run when needed | a skill (core-skill-authoring) |
| a check that must not be skipped (format, secrets, blocking a command) | a hook or a permission rule — CLAUDE.md is context, not enforcement |
| a personal preference | `CLAUDE.local.md` (in `.gitignore`) or `~/.claude/CLAUDE.md` |
| a pitfall from an incident | `docs/project/lessons.md` (core-project-record); it comes back a second time → a proposal for CLAUDE.md |
| references: PRDs, plans, decisions, maps | `docs/project/` read when needed, with a link in CLAUDE.md |

**An agent starting elsewhere** (a multi-repository session, an agent from repo A changes repo B) does not load
the `CLAUDE.md` or `AGENTS.md` of repo B. Rules needed when working from outside (the fork's name, the target branch, required
flags, e.g. `gh -R …`) you also keep where such an agent looks: in the global instructions (`~/.claude/CLAUDE.md`)
or in the README of repo B; a script or a hook enforces a critical rule.

One rule lives in one place. Several AI tools in the team: `AGENTS.md` as the source of truth, and `CLAUDE.md`
with one line `@AGENTS.md` (and possibly rules only for Claude Code below it). How Claude Code loads these files
(subdirectories on demand, imports, AGENTS.md without CLAUDE.md): `references/context-scaling.md`, section 4.

**An ownership map of harness artifacts:** every instructions file, skill, hook, tool contract, permission policy
and sensor has an owner from the domain it concerns (not a central "harness team"), a test in CI, a review cycle
and a person who changes the contract. You add rules like a ratchet: only from a real failure, after a review. A skill
unused for 60–90 days (the factory counts uses from hook logs) you mark for retirement. The measure: the share of artifacts
without an owner and without a test.

## 3. Procedure: the first draft
1. The built-in `/init` or an inspection: the README, the manifest and its scripts, the lint/format/type/test configurations,
   1–2 CI files, two levels of the tree, `git log --oneline -n 30` (the commit convention). Every claim from a file,
   a command or a commit (core-grounding); what you cannot establish, write as a question for the human, not a guess.
2. Order by leverage: hard bans → 3–6 commands (build, test, lint) → conventions with a model file →
   tests → commit and PR → security. No mission, values or introducing the team.
3. No code blocks longer than 1–2 lines (a link to the file) and no definitions of general concepts.
4. Budget: a file below ~200 non-empty lines (Anthropic's recommendation for a CLAUDE.md file); a module file usually 10–40 lines.
5. Notes for people in HTML comments `<!-- … -->` — Claude Code removes them before injecting into the context.

## 4. Procedure: a review (the five-check card)
The script first — **run** it, do not read it:
`python3 .claude/skills/core-agent-instructions/scripts/instructions_lint.py --root .` (or the file path; `--json`).
It counts checks 1, 2, 3 and 5, `@` imports and outdated entries, and in `--root` mode also module files outside the index
and rules copied from the main file. Exit code 1 = at least one `ERROR`. You do check 4 yourself.

| # | Check (`id`) | OK | WARN | ERROR |
|---|---|---|---|---|
| 1 | length (non-empty lines without HTML comments) | ≤200 | 201–500 | >500 |
| 2 | code/configuration blocks > 3 lines (except diagrams) | 0 | 1–2 | ≥3 |
| 3 | intention phrases | 0 | 1–3 | ≥4 |
| 4 | unneeded knowledge: no surprise for the agent, the framework's default behaviour, a definition, sounds like a tutorial, could be a link | 0 | 1–3 | ≥4 |
| 5 | order: critical rules in the first third, no introduction on top | yes | mixed | critical after line 200 / no headings |

- Every finding with `plik:linia`. For every intention a checkable proposal based on a signal from the project
  ("take care of errors" → "handlers return `{ error: { code, message } }`, the model `src/api/errors.ts`"); no signal
  in the repo → a default for the stack marked [assumption].
- Conflicting rules in two files are an error: the model may choose either of them.
- By default only a report. Rearranging sections or cuts — with the human's consent, without changing the content of the rules.

The output schema:
```
Instructions review — <path>   Assessment: <one sentence>
| # | Check | Verdict | Count |      (five rows)
Findings: <check> — file:line — problem — proposal
3 actions with the biggest leverage: 1. … 2. … 3. …
```

## 5. Procedure: updating an existing file
1. `git log -1 --format=%H -- CLAUDE.md` → the last change of the file (`LAST`).
2. `git diff LAST..HEAD --stat -- package.json pyproject.toml .github/ README.md <konfiguracje lint/testów>` —
   what changed since then (especially scripts and commands).
3. Every file and command CLAUDE.md refers to, check that it exists
   (`python3 .claude/skills/core-grounding/scripts/grounding_check.py CLAUDE.md`).
4. Classify the lines: KEEP / FIX / REMOVE / MISSING, each with the `plik:linia` of the source.
5. Show the list and edit pointwise with consent — do not rewrite the whole thing. The human's uncommitted changes in the file = KEEP.
6. After a bigger model change review the rules that work around weaknesses of an older model: some have become unneeded.

## 6. Rule calibration (A/B) — does the rule change anything
1. The same task 3–5 times in a fresh session from the same repo state, **without the rule**. Note: convention breaches,
   time, the number of files read, iterations, cost (if visible).
2. Add the rule in 1–3 sentences in the right place (section 2).
3. Repeat the same runs. The agent got it right without the rule or no improvement → remove the rule.
4. Change one thing at a time (content, place, order). A change of the factory's CLAUDE.md or of a project with personas is
   a change of the agent's configuration — an evaluation as in core-delivery-lifecycle.

## Anti-patterns
- An encyclopedia file: rules from the middle of a long file get lost (models take the middle of a long context into account worst).
- A copy of the documentation or the README; a description of the architecture the agent reads from the code anyway.
- The same rule in three files; a rule in the root and its copy in a module.
- Local memory (automatic memory, `CLAUDE.local.md`) as the only place of the team's agreements.
- Asking in words "read AGENTS.md" instead of the `@AGENTS.md` import — the agent may not open the file.
- An `@plik` import as a way to save — imports load at start and count towards the context.

## Example
Input: a CLAUDE.md of 340 lines; lines 1–40 "About the project and values"; line 287 "never send customer data
to the logs"; a 25-line block from tsconfig; "write clean code" in line 52.
The script's output: `length` WARN (340), `blocks` WARN (1), `intents` WARN (1), `order` ERROR (a critical rule at l. 287,
an introduction on top). Check 4 (by hand): 6 lines describing directories visible in the tree → WARN.
3 actions: (1) the ban on logging customer data to the first section; (2) the tsconfig block → remove it (`strict` is enforced
by the configuration), instead 1 line about the exception the configuration does not show; (3) the introduction down to 2 sentences, remove the directory description,
"clean code" → "public functions in `src/api/` have a return type and handle errors through `AppError`".
After the changes: 190 lines, an A/B calibration for the `AppError` rule (3 runs without and 3 with the rule).

## Checklist
- [ ] every new line passed the inclusion test and answers a recurring agent mistake
- [ ] critical bans on top; the file ≤ ~200 non-empty lines; zero pasted configuration blocks
- [ ] intentions rewritten into behaviour checkable in the diff; one rule in one place, no conflicts
- [ ] rules for parts of the code in a module file or `.claude/rules/` with `paths`; procedures in skills; enforcement in hooks
- [ ] `instructions_lint.py --root .` without ERRORs; references checked with `grounding_check.py`
- [ ] a new rule tested in a fresh session (A/B), an unneeded one removed

## Sources
- Claude Code, "How Claude remembers your project" (code.claude.com/docs/en/memory, accessed 2026-10-10): the goal below
  200 lines per file, the loading order, subdirectories on demand, `@` imports (up to 4 levels, loaded at start),
  `.claude/rules/` with `paths`, AGENTS.md read when there is no CLAUDE.md, removing HTML comments, "when to add".
- Claude Code, "Set up Claude Code in a monorepo or large codebase" (code.claude.com/docs/en/large-codebases, accessed
  2026-10-10): CLAUDE.md in directories, rules per path, a review after bigger model releases.
- J. L. Lulla et al., "On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents", arXiv:2601.20404
  (2026): median time −28.64%, output tokens −16.58% at comparable effectiveness (10 repos, 124 PRs).
- T. Gloaguen et al., "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?",
  arXiv:2602.11988 (2026): context files do not raise effectiveness, and the cost grows by over 20%; repo overviews
  do not help; non-standard project practices do help (abstracts accessed 2026-10-10).
- N. F. Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", arXiv:2307.03172 [unverified
  in this session — a well-known paper, cited after the course].
- The 10xDevs course, ed. 3 (2026), module 1, lesson 4 (agent onboarding, AGENTS.md, rules) and module 4, lesson 1
  (scaling context) — training material (accessed 2026-10-09).

Described in our own words.
