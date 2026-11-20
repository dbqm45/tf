---
name: eng-repo-readiness
description: Use when setting up a project skeleton from the official generator or checking whether an existing repo is ready for agent work — audit, tests, DX, verdict.
metadata:
  review: "2027-10-10"
  catalog: "Use when a repository must become safe and verifiable for agent work. Path A (new project): the skeleton from the official generator named in an accepted stack decision — starter freshness check, a temporary directory, a conflict policy that never overwrites existing files, a bootstrap verification report. Path B (existing project): a read-only audit with the script scripts/readiness_check.py — lockfile, dependency audit command, test runner dry run, CI stages, configuration, four agent-friendliness checks per stack component with paste-ready CLAUDE.md compensations, the developer loop (one setup command, compose with healthchecks, seed, .env.example, related tests, clone-to-green time), a verdict and an ordered fix list. Not for choosing a stack (arch-tech-selection), auditing debt in the code (eng-tech-debt-audit), matching skills to versions (core-stack-sync) or upgrading dependencies (ops-dependency-upgrades)"
  keywords: "gotowość repo, repo gotowe dla agentów, czy agenci mogą pracować w repo, przejmujemy repo, audyt repozytorium, szkielet projektu, postaw szkielet, scaffold, bootstrap, generator projektu, oficjalny generator, sv create, create-vite, create-next-app, starter projektu, porzucony starter, świeżość startera, generator się wywalił, żeby nasze pliki nie zginęły, konflikt plików, .scaffold, lockfile, npm audit, audyt zależności, runner testów, brak testów, testy na sucho, decyzja o stacku, DX, doświadczenie dewelopera, nowa osoba nie umie uruchomić projektu, dwa dni na uruchomienie, onboarding programisty, jedno polecenie setup, make setup, devcontainer, docker compose dla deweloperów, healthcheck, service_healthy, dane startowe, seed, .env.example, zmienne środowiskowe na Slacku, agent nie umie uruchomić testów, testy wymagają Postgresa, testcontainers, testy trwają za długo, testy powiązane, czas od klonu do zielonych testów, repo readiness, is the repo ready for agents, taking over a repository, project skeleton, scaffold from the official generator, abandoned starter, starter freshness, generator crashed, file conflicts, dependency audit, test runner dry run, developer experience, new joiner cannot run the project, one setup command, compose healthcheck, seed data, agent cannot run tests, clone to green time"
---

# Repo readiness — a skeleton from the generator, or an audit of what exists

An agent works safely only in a repo where it can install, run and test the project by itself and where the results
are checkable. This skill either creates such a repo from an official generator (path A) or audits an existing one
(path B). It informs and proposes; it does not change the stack and fixes nothing by itself.

**Overriding rule:** delegate to the authoritative CLI — the project generator, `docker init`, `ng generate`,
`prisma migrate dev`. Remembered syntax and file layouts go stale; never write a skeleton from memory. When the CLI
fails, **stop** and report the command, the exit code and the last output lines; never patch missing files by hand.

## Path A — a new project from the generator
1. **Precondition:** `docs/project/04-architecture/stack-decision.md` with status `accepted`, naming the generator
   command and version. Agreement in the conversation is not enough; no file → refuse in one sentence and point to
   arch-tech-selection. No scaffold without it.
2. **Freshness of the starter** (a team heuristic): `npm view <pkg> version time.modified` or
   `gh api repos/<owner>/<repo> --jq .pushed_at`. Under 3 months — fresh; 3–6 — ageing; over 6 — outdated: a warning,
   not a block, with an official alternative of the same family (e.g. `sv create` instead of a community template).
3. **Scaffold into `.bootstrap-scaffold/`**, never into the repo root. Generator exit code ≠ 0 → STOP: keep the
   directory for inspection, write the report with status `failed`, add nothing by hand.
4. **Move with the conflict policy** (existing files always win):
   - `CLAUDE.md`, `AGENTS.md`, `README.md`, `.claude/`, `docs/project/` — the existing version stays; the generator's
     version goes beside it as `<file>.scaffold`;
   - manifests (`package.json`, `pyproject.toml`) — existing stays, generator version as `.scaffold`, and the report
     lists the differences (scripts, dependencies);
   - `.gitignore` — additive merge without duplicate lines;
   - other files are moved; a name clash → `.scaffold`;
   - a cloned starter: delete its `.git/` before moving;
   - never delete or overwrite human files; `git init` and the first commit are the human's decision.
5. **After the move:** the dependency audit (report only; `npm audit fix` and similar only with consent), the skeleton
   tests, the build.
6. **Report** `docs/project/06-delivery/bootstrap-verification.md`: generator command and version, exit code, moved
   files, `.scaffold` conflicts, `.gitignore` lines added, audit findings direct vs transitive, test and build
   results, next steps (merge or reject each `.scaffold`, `git init`, vulnerability actions). A failed run: command,
   exit code, the last 20 lines, the path of the scaffold directory. Templates: `references/reports.md`.

## Path B — an existing project
Facts before assessment. Run, do not re-implement:
- `python3 .claude/skills/eng-repo-readiness/scripts/readiness_check.py [directory] [--json]` — offline, runs nothing;
  exit 0 no high findings, 1 high findings, 2 invocation error;
- `python3 .claude/hooks/detect_stack.py` — the stack components.

Running the audit or the test listing needs the human's consent (it installs or executes project code).

1. **Foundation:** the ecosystem's lockfile (`requirements.txt` alone is a weak substitute); the dependency audit,
   direct vs transitive (`npm audit --json`, `pip-audit --format json`, `cargo audit --json`, `govulncheck -json ./...`,
   `bundle audit check --update`, `composer audit --format json` on Composer ≥ 2.4,
   `dotnet list package --vulnerable --include-transitive`); dependencies one or more majors behind. A family without a
   built-in audit (Java, Dart) is reported as **"skipped"**, never "0 findings". Critical audit hits raise the verdict
   by hand — the script does not know vulnerabilities.
2. **Execution environment:** the test runner and a dry run that lists tests without executing them (`npx vitest list`,
   `npx jest --listTests`, `pytest --collect-only -q`, `cargo test --no-run`, `go test -list . ./...`,
   `dotnet test --list-tests`, `mocha --dry-run`); CI stages present (lint, test, build, types, security);
   configuration: missing `.gitignore` high, TypeScript without `strict` high, no linter or formatter medium,
   no `.editorconfig` or `.env.example` low.
3. **Four agent-friendliness checks per stack component**, each with evidence from a file or config:
   - **types** — explicit data contracts (TS strict, typed Python, schemas at the API);
   - **conventions** — established places for routes, tests and config;
   - **popularity within its language family** (Django among Python frameworks, not Django versus React);
   - **current versioned documentation**.
   Stack verdict: `ready` / `ready-with-compensation` / `high-friction`. A failed check gets a **compensation**:
   concrete rules to paste into CLAUDE.md (e.g. "routes live in `src/routes/<resource>.js`; middleware order: auth →
   validate → handler; every route has a test in `test/routes/`"), never "add documentation".
4. **The developer loop** (`references/developer-loop.md`):
   - one idempotent start command (`make setup`, `just setup`, `task setup` or `npm run setup`) that installs from the
     lockfile (`npm ci`, `uv sync`, `poetry install --sync`), starts services (`docker compose up -d --wait`), runs
     migrations and an idempotent synthetic seed; plus `make dev` and `make test`; documented in the README quick start
     and in CLAUDE.md/AGENTS.md;
   - services in `compose.yaml` pinned to production versions, with a `healthcheck` and `depends_on` with
     `condition: service_healthy` — or Testcontainers, so tests do not depend on compose;
   - a devcontainer only when tools are hard to install or Codespaces are used; otherwise compose plus a version
     file (`.nvmrc`, `.python-version`, `mise.toml`);
   - `.env.example` lists every variable with blank or dummy values; a real-looking key there is a **high** finding —
     shown by variable name only, and it must be revoked because it is in history;
   - external services stubbed or in sandbox mode (Stripe test mode, Mailpit);
   - fast feedback: a related-tests command (`vitest related`, `jest --findRelatedTests`, `nx affected -t test`,
     `pytest --lf` or testmon, `go test ./pkg/...`), fast and slow suites split (`make test-unit` / `make test-int`), and
     CLAUDE.md saying what to run after a change and what before handover.
5. **Measure clone-to-green time** (with consent: it installs and starts services; no real secrets): a fresh clone
   into a temporary directory, follow only README/CLAUDE.md, `time make setup && time make test`; record the total,
   every moment you had to guess or ask, and every manual step — each is a fix. An indicative team goal: setup under
   15 minutes and no manual steps except personal keys [assumption].
6. **Verdict and fixes.** Project verdict: `critical` (no test runner, or ≥ 3 high findings) / `needs-attention` /
   `healthy`. The fix list is ordered by impact on the agent (no tests outranks a low audit alert); each fix says what,
   why it matters for the agent, the command, and the effort: quick (< 5 min), medium (15–30 min), large (> 1 h).
   The verdict informs and never blocks or recommends changing the stack.
7. **Report** `docs/project/07-review/<date>-repo-readiness.md`: TL;DR with both verdicts and fix #1, the facts table
   with evidence, the four-checks table, paste-ready compensations, the fixes table, "what was not checked". Every
   number has evidence (a file or a dated command) or is marked "not checked". Template: `references/reports.md`.

## Example
Taking over a Flask API (Python 3.12, `requirements.txt` only, pytest in use, CI runs only `flake8`).
- Script: family python, lockfile weak (`requirements.txt`, no hashes) — medium; runner pytest,
  `pytest --collect-only -q` lists 212 tests; CI: lint ✓, test ✗, build ✗; no formatter — medium;
  `.env.example` has `STRIPE_SECRET_KEY` with a real-looking value — high.
- With consent: `pip-audit --format json` — 1 high in a transitive dependency, 0 direct.
- Checks for Flask: types ✗ (no annotations, no request schemas), conventions ✗ (routes in three styles), popularity ✓,
  docs ✓ → `ready-with-compensation`; compensations for CLAUDE.md: "new endpoints in `app/api/<resource>.py` with a
  marshmallow schema; run `pytest tests/api -q` after a change".
- Project verdict `needs-attention` (one high finding). Fixes: 1) revoke and blank the key in `.env.example` (quick);
  2) add a `pytest` stage to CI (quick); 3) `uv` with a lockfile (medium); 4) bump the transitive package through its
  parent after review (medium); 5) ruff format in pre-commit (quick, eng-local-quality-gates).

## Checklist
- [ ] path A only with an accepted stack decision file; scaffold in `.bootstrap-scaffold/`; existing files win
- [ ] generator failure → stop and report, nothing added by hand
- [ ] path B: facts from the script and dated commands; audit and test listing with consent; "skipped" where no audit exists
- [ ] four checks per component with evidence; compensations as paste-ready CLAUDE.md rules
- [ ] developer loop: one command, healthchecks, seed, `.env.example`, related tests, clone-to-green measured
- [ ] verdicts, fixes ordered by impact on the agent, "not checked" listed

## Sources
- npm CLI `npm view`, `npm audit` (docs.npmjs.com); pip-audit (pypi.org/project/pip-audit); cargo-audit (rustsec.org);
  govulncheck (pkg.go.dev/golang.org/x/vuln/cmd/govulncheck); bundler-audit (github.com/rubysec/bundler-audit);
  Composer `audit` command, Composer 2.4+ (getcomposer.org/doc/03-cli.md#audit), also described on php.watch;
  `dotnet list package --vulnerable` (learn.microsoft.com) — accessed 2026-10-10.
- Docker Compose: `healthcheck`, `depends_on` `condition: service_healthy`, `up --wait` (docs.docker.com/compose,
  accessed 2026-10-10).
- Test listing flags verified on the named runners' current versions, 2026-10-10.
