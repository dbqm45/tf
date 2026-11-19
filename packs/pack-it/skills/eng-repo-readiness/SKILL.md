---
name: eng-repo-readiness
description: Use when a repo must be ready for agents — a skeleton from a generator or an audit of lockfile, tests, CI.
metadata:
  review: "2027-10-10"
  catalog: "Use when a repository must be ready for safe, verifiable agent work — a new project: a skeleton from the official generator based on the stack decision, starter freshness, a temporary directory and a file conflict policy, a report with the exit code; an existing project: a read-only audit (lockfile, the dependency audit command, a dry run of the test runner, CI stages, configuration, the four stack gates with compensation in CLAUDE.md, the developer loop: one start command, local services with a healthcheck, seed data, related tests, time from clone to green tests), a verdict and a list of fixes. Script scripts/readiness_check.py. Not for choosing a stack (arch-tech-selection), auditing debt in the code (eng-tech-debt-audit), matching skills to versions (core-stack-sync) or upgrading dependencies (ops-dependency-upgrades)."
  keywords: "gotowość repo, repo gotowe dla agentów, czy agent może tu pracować, przejmujemy repo, postaw szkielet, szkielet projektu, scaffold, bootstrap, generator projektu, starter, create-app, nowy projekt od zera, audyt repo, health check repo, brak lockfile, brak testów, runner testów, porzucony starter, generator zwrócił błąd, developer experience, DX, uruchomienie projektu lokalnie, nowa osoba nie może uruchomić projektu, onboarding programisty, devcontainer, docker compose dla deweloperów, make setup, justfile, dane startowe, seed, agent nie potrafi uruchomić testów, testy wymagają bazy, czas od klonu do zielonych testów, testy trwają za długo, repo readiness, repo ready for agents, can an agent work here, we are taking over a repo, set up a skeleton, project skeleton, project generator, new project from scratch, repo audit, no lockfile, no tests, test runner, abandoned starter, the generator returned an error, running the project locally, a new person cannot run the project, developer onboarding, docker compose for developers, seed data, the agent cannot run the tests, tests require a database, time from clone to green tests, tests take too long"
---

# Repository readiness for agent work

The skill's question: **can an agent work in this repo safely and verifiably starting tomorrow?** Safely means it will not
overwrite the human's files and will not install anything silently. Verifiably means it has a lockfile, tests run with one
command, CI and clear conventions. A new project gets a skeleton (path A), an existing one — an audit (path B).

## Overriding rule: delegate to the authoritative CLI
- If a tool exists that does the task (a project generator, `docker init`, `ng generate`, `prisma migrate dev`),
  the agent calls it instead of recreating files from memory. The model's memory is often syntax from two releases ago.
- When the authoritative CLI returns an error, the agent stops too: **it does not add the missing files by hand**, it does not
  "finish" the skeleton. It reports the command, the exit code and the last lines of the output.

## Path A — a new project (skeleton)
**Precondition:** an accepted stack decision (`docs/project/04-architecture/stack-decision.md`, status
`accepted`) with the generator command and its version. No file → refusal and a referral to arch-tech-selection. Agreements
from a conversation do not replace the file.
1. **Generator freshness** (a warning, not a block):
   - `npm view <generator-package> version time.modified` or `gh api repos/<owner>/<repo> --jq .pushed_at`;
   - < 3 months fresh · 3–6 months ageing · > 6 months outdated → show it to the human and propose an official
     alternative from the same family.
2. **Skeleton into a temporary directory** `.bootstrap-scaffold/` (never directly into the repo root). A generator with an exit code
   ≠ 0 → STOP: the directory stays for inspection, a report with the status `failed`.
3. **Moving with a conflict policy** (table below). A cloned starter: remove its `.git/` before moving.
   You do not delete or overwrite the human's files.
4. **After moving:** a dependency audit (commands:
   `.claude/skills/ops-supply-chain-security/references/dependency-audit.md`), tests and a build of the skeleton. The audit does not fix anything itself — `npm audit fix` etc. only with consent.
5. **Report** `docs/project/06-delivery/bootstrap-verification.md`: the generator command and version, the exit code,
   the moved files, `.scaffold` conflicts, the audit result (direct / transitive), the test and build result,
   next steps. `git init` and the first commit are the human's decision.

| File in the skeleton | When it already exists in the repo |
|---|---|
| `CLAUDE.md`, `AGENTS.md`, `README.md`, `.claude/`, `docs/project/` | the existing one wins; the generator's version next to it as `<file>.scaffold` |
| `package.json`, `pyproject.toml` and other manifests | the existing one wins, `<file>.scaffold` + a list of differences in the report for a decision |
| `.gitignore` | an additive merge: the generator's lines that are missing, without duplicates |
| other files | moved; a name conflict → `.scaffold` |

## Path B — an existing project (read-only audit)
Facts first, then the assessment:
`python3 .claude/hooks/detect_stack.py` and **run** `python3 .claude/skills/eng-repo-readiness/scripts/readiness_check.py [directory] [--json]`
(families, lockfile, audit command, the runner and its dry-run command, CI stages, configuration, instruction files, the developer
loop; exit code 1 =
high-severity findings). The script runs nothing — you run the audit and the test listing yourself, with the human's consent.
1. **Foundation:** a lockfile appropriate for the ecosystem (`requirements.txt` is a weak substitute), the result of the dependency
   audit (direct separately from transitive), dependencies behind by ≥ 1–2 major versions (major gaps only).
   A family without a built-in audit (Java, Dart) → "skipped", **never "0 findings"**.
2. **Execution environment:** the test runner and a dry run (`npx vitest list`, `npx jest --listTests`,
   `pytest --collect-only -q`, `cargo test --no-run`, `go test -list . ./...`, `dotnet test --list-tests`); CI stages
   lint / test / build / types / security (✓/✗); configuration: `.gitignore` (high), TypeScript without `strict`
   (high), no linter or formatter (medium), `.editorconfig` and `.env.example` (low).
3. **The four stack gates per component** — with evidence (a file, configuration) for every assessment:
   **types** (explicit data contracts in the code) · **conventions** (established places for routing, tests, configuration) ·
   **popularity within the language family** (Django among Python frameworks, not against React) · **current,
   versioned documentation**. For a failed gate: **rules for CLAUDE.md ready to paste**, e.g. "routes
   in `src/routes/`, each exports `router`; middleware in the registration order in `src/app.js`". Not "add
   documentation".
4. **Developer loop (DX):**
   - one start command (`make setup` / `just setup`), described in the README and CLAUDE.md;
   - services (database, Redis, queue) in `compose.yaml` with a healthcheck, `docker compose up -d --wait`, or
     Testcontainers;
   - idempotent seed data with synthetic data and `.env.example` without real keys;
   - a command for the tests related to a change (`vitest related`, `jest --findRelatedTests`, `nx affected`,
     `pytest --lf`) written in CLAUDE.md as the one the agent runs after every change.
   The facts come from the script's `dx` section. The measure is the **time from clone to green tests**: a fresh clone in a temporary
   directory, following only the README, `time make setup && time make test` — with the human's consent, the result in the report.
   Procedure and thresholds: `references/developer-loop.md`.
5. **Verdict** (it informs, it does not block; it never recommends changing the stack):
   - stack: `ready` / `ready-with-compensation` / `high-friction`;
   - project: `healthy` / `needs-attention` / `critical` (critical vulnerabilities, no test runner, ≥ 3 high gaps).
6. **List of fixes** in the order of impact on the agent's work (no tests > a low audit alert): what · why for the
   agent · a concrete command · effort (quick < 5 min / medium 15–30 min / large > 1 h). You fix nothing yourself.

Report: `docs/project/07-review/<date>-repo-readiness.md` (core-project-record). The template of both reports:
`references/reports.md`.

## Example
**Situation:** "We are taking over an API in Express (JavaScript, no TS). Can agents work here?"
**Result:** `readiness_check.py` — `package-lock.json` exists, `npm audit --json` to be run, test runner:
NONE (high), CI only `npm run build`, `.gitignore` exists, a linter exists, no formatter (medium). Audit (with consent):
2 high in transitive dependencies, 0 in direct ones. Gates: types ✗, conventions ✗, popularity ✓,
documentation ✓ → `ready-with-compensation`; rules for CLAUDE.md: the layout of route directories, the middleware order, the error
handling pattern (`next(err)` + one handler), JSDoc on public functions. Project: `critical` (no runner).
Fix no. 1: a test runner with one smoke test (medium); no. 2: a test stage in CI; no. 3: transitive
vulnerabilities — we wait for the maintainer or `overrides` after a review.

## Checklist
- [ ] (A) the generator from the accepted decision, not from memory; freshness checked; a temporary directory
- [ ] (A) the human's and the factory's files untouched, conflicts as `.scaffold`; a generator error = stop and report
- [ ] (B) facts from the script and commands before the assessment; every assessment with `file` evidence or a command
- [ ] (B) a skipped audit described as "skipped", not "0"; direct separately from transitive
- [ ] compensations as concrete rules for CLAUDE.md; the test runner works or is fix no. 1
- [ ] (B) one start command, services with a healthcheck, seed data, related tests in CLAUDE.md; the time from
  clone to green tests measured or recorded as "not measured"
- [ ] the report in `docs/project/`; nothing installed or fixed without consent

## Sources
- 10xDevs course, ed. 3 (2026), lesson 4.1 (choosing a stack) and module 1, lessons 2 and 5 (starting a project with an agent,
  deployment) — training material (accessed 2026-10-09); described in our own words.
- CLI documentation checked 2026-10-10 in an isolated directory: `vitest list` (Vitest 3.2.4), `mocha --dry-run`
  (Mocha 11.7.1), `pip-audit --format json` (pip-audit 2.10.1), `npm view <package> time.modified` (npm 10).
- Composer: `composer audit` since version 2.4 — [php.watch](https://php.watch/articles/composer-audit) (accessed 2026-10-10);
  govulncheck: reports vulnerabilities reachable from the code — [pkg.go.dev](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
  (accessed 2026-10-10).
