# Scaling an agent's context in a big project

> **Contents:** 1. Three kinds of context — three places · 2. Four failures of an overgrown file · 3. The maturity ladder and the signals for moving up · 4. How Claude Code loads instruction files (checked state) · 5. A CLAUDE.md in a module — the pattern and the index in… · 6. A module file or a rule with `paths` · 7. Maintaining and reviewing rules · 8. Many repositories · 9. The result and an example

The question is not "what should the agent know", but "what should it know **now**". Permanent context takes attention from the task.

## 1. Three kinds of context — three places
| Kind | What it is | Where |
|---|---|---|
| conventions | how we work, what cannot be seen from the code | `CLAUDE.md` (root + modules), `.claude/rules/` |
| references | PRDs, plans, research, decisions, code maps | `docs/project/` (core-project-record) — read when needed |
| procedures | repeatable steps with decision points | skills, commands |

The main `CLAUDE.md` is a table of contents, not an encyclopedia: commands, global conventions, pointers to the rest.

## 2. Four failures of an overgrown file
1. **It crowds out the task** — it takes context that should belong to the current work.
2. **It dilutes** — when everything is important, nothing is; rules from the middle get lost.
3. **It rots** — rules age faster than anyone reviews them; an outdated rule does more harm than none.
4. **It cannot be checked** whether the agent follows it — too many rules for one task.

The order of repair: hygiene first (cut per the inclusion test in SKILL.md), only then structure (splitting).

## 3. The maturity ladder and the signals for moving up
You move up on demand, not in order and not "just in case".
1. **Root `CLAUDE.md` + `docs/project/`** — the default; for an MVP and small repos for as long as possible.
2. **A `CLAUDE.md` in a module + an index in the root** — the module has its own detailed conventions irrelevant to the rest or
   a separate owner.
3. **The module's own documentation directory** (the module's plans, decisions) — when a separate team runs it or the work
   in the module is intensive and long.

Signals for moving up (at least one, with the evidence written in the result):
- the root above ~200 non-empty lines despite hygiene (the `instructions_lint.py` script);
- the agent repeats a mistake in a module despite a rule in the root (write down specific cases: the date, the file, what it did);
- for every piece of work in the module you give the same references by hand;
- the module has its own deploy, its own owner in CODEOWNERS or a different stack.

The number of directories and the feeling "this is a big application" are **not** a signal. Split by ownership boundaries, not size.
Do not create a `CLAUDE.md` for a young module that is still changing — a slowly changing file does not hold
quickly changing facts (file names in motion, numbers, versions).

## 4. How Claude Code loads instruction files (checked state)
Source: code.claude.com/docs/en/memory and …/large-codebases, accessed 2026-10-10. The behaviour depends on the version —
when in doubt check `/context` (the "Memory files" list) in the current session.
- **At start**: `CLAUDE.md` and `CLAUDE.local.md` from the working directory and all directories above it, and also
  `~/.claude/CLAUDE.md` and the file managed by the organisation. The files are **concatenated**, not overwritten; the one closer to the working
  directory is read later. The project file can be in `./CLAUDE.md` or `./.claude/CLAUDE.md`.
- **On demand**: a `CLAUDE.md` from subdirectories loads only when the agent reads files in that subdirectory. Starting
  the session from the root = the module file may not yet be in context when the agent plans. A critical rule of a module →
  start the session in the module or point to the file explicitly in the instruction or the subagent's brief.
- **`@ścieżka` imports**: expanded at start together with the file that contains them; relative paths counted from
  the file with the import; up to 4 levels of nesting. They organise, but **do not reduce** the context cost. An import
  in backticks (`` `@README` ``) and in a code block is not executed. An import from outside the working directory
  needs the human's one-time consent.
- **`.claude/rules/*.md`**: without a `paths` field they load at start like `.claude/CLAUDE.md`; with a `paths` field
  (a list of globs) — only when the agent reads or edits a matching file. `paths` is the only field Claude Code
  reads from a rule's header; invalid YAML = a rule loaded always.
- **AGENTS.md**: newer versions of Claude Code read `AGENTS.md` themselves, but by default **only when in the working
  directory and above there is no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md`**. When both files exist, Claude reads
  only `CLAUDE.md` — which is why the pattern "AGENTS.md as the source of truth, CLAUDE.md with `@AGENTS.md`" works regardless of
  version and settings. Note: adding your own `CLAUDE.local.md` in a repo based on AGENTS.md turns off reading
  AGENTS.md (changed in the "Project instructions" setting in `/config`). A link `CLAUDE.md → AGENTS.md` works,
  but on Windows git may check it out as a plain text file — an import is safer there.
- **Other tools** (Codex, Copilot): they read `AGENTS.md` from the directory tree; check the details of precedence
  in their documentation for the version in use [unverified in this session].
- **Size**: a file above the recommended length gives a warning at start; Claude Code skips a file bigger than
  4 MiB. Automatic memory (`~/.claude/projects/<projekt>/memory/MEMORY.md`) loads only the first 200 lines or
  25 KB — those are the machine's notes, not a place for the team's rules.
- **After `/compact`**: the root `CLAUDE.md` is re-read from disk; module files and rules with `paths` come back
  only when the agent touches a matching file again. An instruction given only in the conversation disappears.
- **A monorepo with other people's packages**: `claudeMdExcludes` in `.claude/settings.local.json` (globs on absolute
  paths) skips the instruction files of directories you do not work in.

## 5. A CLAUDE.md in a module — the pattern and the index in the root
- The first line: "Only the `<module>` context. Rules for the whole repo: the main CLAUDE.md."
- Only what cannot be inferred from the root or from the module's code: pitfalls (the real entry point, forbidden
  APIs, the required logger), anti-patterns, the module's commands (tests, migrations). Zero copies of the root's rules.
- 10–40 lines; a longer module file is a signal that part of the content is a reference (to `docs/`) or a procedure (to a skill).
- The root ends with a **"Modules with their own CLAUDE.md"** section: `path — one sentence of scope`. The
  `instructions_lint.py --root .` script reports a module file outside that index and lines copied from the root.
- The owner of a module file is the module's owner; changes go through review in a PR like documentation.

## 6. A module file or a rule with `paths`
| Approach | Where it lives | Loads | When |
|---|---|---|---|
| a `CLAUDE.md` in a directory | next to the code | at start from that directory or when the agent reads a file there | the directory's owner keeps their own conventions |
| a rule `.claude/rules/x.md` with `paths` | centrally in the root | when the agent reads/edits a matching file | all conventions in one place or the same rule for scattered files (e.g. `**/*.test.ts`) |
| a skill in `<moduł>/.claude/skills/` | in the module | when the task fits the description | a module's procedure (tests, migrations), not a permanent convention |

## 7. Maintaining and reviewing rules
A review every month or quarter (and after a bigger model release), five questions for each rule:
1. Would the agent break it without it? (the A/B calibration in SKILL.md, section 6)
2. Does it follow from the code, the linter, types or a hook? → remove it.
3. Is it checkable in the diff?
4. Is it current (do the paths, commands, versions exist)?
5. Does it duplicate or contradict another rule in another file?
An entry in the result: the review date, the rules removed and added with a reason. A `Stop` hook that proposes CLAUDE.md
fixes after a session is an option for mature teams — the proposal goes to the human, not straight into the file.

## 8. Many repositories
Three layers, from the simplest:
1. **Shared rules and skills in one source repo**, versioned (SemVer, core-semver).
2. **Distribution with updates**: a package → a CLI → a plugin or an MCP server (increasing complexity). Each repo still has
   its own short `CLAUDE.md` with local agreements. Installer details: `.claude/skills/core-skill-authoring/references/team-distribution.md`.
3. **Visibility of other repos during work**: generated contracts (OpenAPI, AsyncAPI, protobuf, GraphQL SDL),
   contract test packages, documentation generated in CI — instead of a meta-repo describing everything by hand
   (it ages fastest). A snapshot of a whole repo into one file only ad hoc, for one task.

## 9. The result and an example
The result of the structure decision: `docs/project/04-architecture/context-architecture.md` — the rung of the ladder, the signals
with evidence, an index of instruction files (path — scope — owner), the date of the next review.

Example: a monorepo with the packages `api`, `web`, `cli`; the root 340 lines; the agent used `console.log` 3× in `cli` despite a rule
in the root. Hygiene: 90 lines duplicating lint and the directory description cut → the root 250. A signal (a repeated mistake in a module
with three cases) → `packages/cli/CLAUDE.md`, 30 lines (the entry point `src/main.ts`, the logger `src/log.ts`,
a ban on the global `fetch`), the CLI rules removed from the root → the root 190 lines + the "Modules with their own CLAUDE.md" section.
`api` and `web` stay on rung 1. A check after a week: 0 new `console.log` in 5 tasks in `cli`.
