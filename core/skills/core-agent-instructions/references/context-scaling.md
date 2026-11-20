# Scaling agent instructions — modules, loading, many repositories

> **Contents:** 1. Why one file stops scaling · 2. When to split, and along which line · 3. The module file pattern · 4. How Claude Code loads instruction files · 5. Module file, path-scoped rule or module skill · 6. Maintenance cycle · 7. Ownership of instruction artifacts · 8. Many repositories · 9. Recording the decision (with a worked example)

## 1. Why one file stops scaling
Three kinds of material compete for the same file: conventions (always-true rules), reference material (how a
subsystem works) and procedures (how to do a recurring task). Only conventions belong in an instruction file;
reference goes to `docs/project/`, procedures to skills, and the root file becomes a table of contents. A file that
keeps everything pushes the task out of the context, dilutes the rules that matter, goes stale faster than anyone
reviews it, and makes adherence impossible to check. The middle of a long context is used worst (Liu et al.). Fix
hygiene first (SKILL.md §1, §4), restructure only after that.

## 2. When to split, and along which line
Split along **ownership**, the way code is split between teams (Conway's law), not along size or directory count.
Signals that a split pays off — each with dated evidence:
- the root file stays over ~200 non-empty lines after the hygiene pass;
- the agent repeats the same mistake inside one module (cases with dates);
- the same reference is pasted into prompts by hand every time;
- a module has its own deploy, owner or stack.
Not signals: "the app is big", the number of directories. A young module whose code changes weekly gets no file of its
own yet — its rules would rot before they help.
Typical steps: root file + `docs/project/` → module files with an index in the root → a module that owns its docs
directory as well.

## 3. The module file pattern
- First line: what it covers and that the root file applies too ("Rules for `packages/cli`; root `CLAUDE.md` applies.").
- Only what cannot be inferred: module pitfalls, forbidden APIs, the required logger or client, module commands.
- No copies of root lines (`instructions_lint.py --root` reports them as `repo.duplicates`).
- 10–40 lines; more → move it to docs or a skill.
- The root file gets a section "Modules with their own CLAUDE.md" with one line per file: `path — scope`.
- The module's owner owns the file; changes go through PRs like code.

## 4. How Claude Code loads instruction files
From the Claude Code docs "How Claude remembers your project" and "Set up Claude Code in a monorepo or large codebase"
(code.claude.com, accessed 2026-10-10 — re-check after upgrades).
- **At start:** `CLAUDE.md` and `CLAUDE.local.md` from the working directory and every parent directory, plus
  `~/.claude/CLAUDE.md` and the managed (organisation) file, concatenated. The project file may sit at `./CLAUDE.md` or
  `./.claude/CLAUDE.md`.
- **On demand:** a `CLAUDE.md` in a subdirectory loads only when the agent reads files there. A session started at the
  root may plan without the module's rules — start in the module, or point the agent to the file.
- **Imports:** `@path` expands at start, relative to the importing file, up to 4 levels deep; not inside backticks or
  code blocks; an import outside the working directory needs one-time approval. Imports do not reduce cost — the
  imported text counts in full.
- **`.claude/rules/*.md`:** without `paths` they load at start; with `paths` (a list of globs) only when a matching file
  is read or edited. `paths` is the only header field read; invalid YAML means the rule loads always.
- **AGENTS.md:** newer Claude Code reads it only when none of `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`
  exists — adding a `CLAUDE.local.md` to an AGENTS.md-only repo silently drops it. "Project instructions" in `/config`
  and `/context` show what was loaded. A `CLAUDE.md` symlinked to `AGENTS.md` works, but git on Windows may check out
  a text file instead → prefer `@AGENTS.md`. Other tools (Codex, Copilot) read `AGENTS.md` from the tree; their
  precedence rules are [unverified].
- **Size:** a warning above the recommended length; files over 4 MiB are skipped.
- **Auto memory** (`~/.claude/projects/<project>/memory/MEMORY.md`): only the first 200 lines / 25 KB load.
- **After `/compact`:** the root file is read again; module files and path rules return when a matching file is
  touched; instructions given only in the conversation are gone.
- **`claudeMdExcludes`** in `.claude/settings.local.json` skips other teams' directories in a large repo.

## 5. Module file, path-scoped rule or module skill
| Choose | When |
|---|---|
| module `CLAUDE.md` | rules owned by one directory and its team |
| `.claude/rules/x.md` with `paths` | a convention kept in one central place, or one that spans scattered files (`**/*.test.ts`, `**/migrations/*.sql`) |
| module skill | a module procedure needed occasionally (release of the CLI, regenerating a client) |

## 6. Maintenance cycle
Monthly or quarterly, and after every major model release. For each rule ask:
1. Would the agent break it without the line?
2. Can the agent derive it from code, linter, types or a hook?
3. Can a breach be seen in a diff?
4. Is it still true?
5. Does it duplicate or contradict another file?
Write the review date and what was removed or added (the project record). An optional Stop hook may propose fixes to
the file — as a proposal for the human, never an automatic edit.

## 7. Ownership of instruction artifacts
Treat instruction files, skills, hooks, tool contracts, permission policies and sensors as owned artifacts, as service
ownership works for code: each has an owner in the domain (not a central team), a CI check, a review cycle and a named
person for contract changes. Rules are added from real failures after review, and rarely loosened. Retire skills nobody
uses (the factory's hook logs show usage). A useful health number: the share of artifacts without an owner or a test.

## 8. Many repositories
- Shared rules and skills live in one versioned source repository (core-semver) and are distributed — a package, a CLI,
  then a plugin or MCP server — while each repo keeps a short local file of its own.
  Distribution mechanics: `.claude/skills/core-skill-authoring/references/team-distribution.md`.
- Cross-repo facts come from generated contracts (OpenAPI, AsyncAPI, protobuf, GraphQL SDL), contract-test packages and
  CI-generated docs, not from a hand-maintained meta-repository. A snapshot of all repos is for one-off analysis only.

## 9. Recording the decision (with a worked example)
Write the outcome to `docs/project/04-architecture/context-architecture.md`: the step chosen (§2), the signals with
evidence, the index (`path — scope — owner`) and the next review date.

Worked example. A repository holds `services/billing` (Go), `services/notify` (TypeScript) and `infra/` (Terraform).
The root file has 260 non-empty lines after hygiene. Evidence: three PRs in October (2026-10-03, -11, -24) where the
agent ran `terraform apply` locally in `infra/` instead of opening a plan PR; billing has its own on-call owner; notify
was created two weeks ago.
Decision: `infra/CLAUDE.md` (18 lines: "never `apply` locally — plans go through CI", the workspace naming, the
`make plan ENV=staging` command) and `services/billing/CLAUDE.md` (22 lines: money as integer cents, the idempotency-key
rule, the required tracing client). No file for `notify` yet. A path rule `.claude/rules/migrations.md` with
`paths: ["**/migrations/*.sql"]` for the cross-service migration convention. Root file trimmed to 170 lines with a
"Modules with their own CLAUDE.md" section listing the two files and their owners. Next review: 2027-01-15.

## Sources
- Anthropic, Claude Code docs: "How Claude remembers your project", "Set up Claude Code in a monorepo or large
  codebase", "Settings" (code.claude.com, accessed 2026-10-10).
- Liu et al., "Lost in the Middle: How Language Models Use Long Contexts", arXiv:2307.03172 (2023).
- M. Conway, "How Do Committees Invent?", Datamation, 1968 (Conway's law).
