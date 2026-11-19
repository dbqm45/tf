# The developer loop (Developer Experience)

The developer loop is the path from cloning the repository to a running application and green tests, and then from
a change to the tests' answer. For an agent it is a condition of verifiable work. An agent that cannot set up the database guesses
or skips the tests. An agent that waits 6 minutes for the whole suite after every change has fewer attempts per task and a higher
cost.

## 1. One start command
- `make setup` / `just setup` / `task setup` (or `npm run setup`) does everything a fresh clone needs:
  installs dependencies from the lockfile (`npm ci`, `uv sync`, `poetry install --sync`), starts the services
  (`docker compose up -d --wait`), applies migrations and loads seed data.
- Next to it there is `make dev` (the application with reloading) and `make test` (the whole suite). The same names in every
  repository of the team.
- Write the commands in the README (a "Quick start" section) and in CLAUDE.md or AGENTS.md (the commands section). The agent reads them
  instead of guessing.
- The command is idempotent: a second run breaks nothing.

## 2. Local services
- Service dependencies (PostgreSQL, Redis, a queue, a search engine) in `compose.yaml` with the same versions as in production.
- **A healthcheck** on every service and `depends_on: { db: { condition: service_healthy } }`. In the start
  command `docker compose up -d --wait`. Without this the tests start before the database and fail at random.
- Integration tests can instead start the services themselves: Testcontainers (Java, .NET, Go, Node, Python). Then
  the tests do not depend on whether someone ran compose.
- A devcontainer (`.devcontainer/devcontainer.json`) pays off when the tools are hard to install (several
  languages, native libraries, specific CLI versions) or the team works in Codespaces. With a simple stack compose
  and a version manager (`.nvmrc`, `.python-version`, `mise.toml`) are enough.

## 3. Seed data and development secrets
- The seed data script is idempotent and creates **synthetic** data: a few users with roles,
  sample records for the main flows. Never a copy of production (arch-privacy-compliance).
- `.env.example` has all the variables with empty values or obvious dummies
  (`DATABASE_URL=postgres://dev:dev@localhost:5432/app`). A real key in this file must be revoked, because it is
  in the git history (ops-secrets-identities).
- In local work external services are replaced by dummies or the provider's sandboxes (Stripe in test mode, a local
  SMTP server such as Mailpit). The agent does not need real keys to run the tests.

## 4. A fast test answer
- The tests related to a change: `npx vitest related <files> --run`, `npx jest --findRelatedTests <files>`,
  `npx nx affected -t test`, `pytest --lf` or `pytest-testmon`, `go test ./<package>/...`. The whole suite before
  a commit or in CI.
- A split into fast (unit, seconds) and slow (integration, e2e) with separate commands
  (`make test-unit`, `make test-int`). Write in CLAUDE.md which suite the agent runs after a change and which before
  handing over the work.
- Local gates (a post-edit hook, pre-commit) are described by eng-local-quality-gates.

## 5. The measure: from clone to green tests
Measure it instead of judging by eye. Record the result and the date in the readiness report.
1. A fresh clone into an empty temporary directory, without the project's caches:
   `git clone <repo> /tmp/clone-check && cd /tmp/clone-check`.
2. Follow only the README and CLAUDE.md, without knowledge from your head, and measure the time: `time make setup && time make test`.
3. Record in the report:
   - the total time;
   - every place where you had to guess or ask the human;
   - manual steps.
   - Every manual step is a fix on the list.
4. An indicative goal: setup under 15 minutes on an ordinary machine, zero manual steps apart from entering your own
   keys into `.env`. This is a team goal, not an industry norm [assumption — adjust to the project].

The measurement runs the installation and the services, so you do it with the human's consent, in a temporary directory, without real
secrets.

## 6. Facts from the script
`scripts/readiness_check.py` returns the `dx` section:
- `setup` — detected start commands (`make`/`just`/Taskfile, `dev`/`setup` scripts, a section in the README);
- `services_needed` — services that follow from the dependencies (the `pg` driver → postgres, `ioredis` → redis…);
- `services`, `services_without_healthcheck` — services from compose;
- `devcontainer`;
- `related_tests` — the command for the tests related to a change for the detected runner.

Findings in the `dx` area have severities:

| Finding | Severity |
|---|---|
| a value that looks like a real secret in `.env.example` (only the variable name in the output) | high |
| no start command | medium |
| services without a local environment | medium |
| a dependent service without a healthcheck | low |
| a database without seed data | low |

The script does not measure time and runs nothing — the measurement from point 5 belongs to the agent, with the human's consent.
