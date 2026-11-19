# The factory loop — task → PR on request

The `/tf` command (or the `tf` agent) takes one task and carries it to one PR: a specification, a plan, tests, code,
verification with evidence, commits and a cost report. You start it with `/tf …` or with an ordinary sentence in which
you commission a task ("deliver EBO-1236", "add a session export to CSV"); for a question or a small fix the factory
does not start the loop, and when it is not sure — it asks. It is part of the factory's core, so it works in every installation.
First time with the factory? Start with the "Start here" section in `.tf/factory/GUIDE.md`.

## What for
- **It fits:** a story with acceptance criteria that can be checked with a test; the change fits in a few
  slices (up to 5) and in one PR; the repository has tests and verification commands (CLAUDE.md).
- **It does not fit:** conceptual work (what to build, architecture from scratch), product decisions along the way,
  access to production, a story without acceptance criteria. Then you work with a persona, and the loop comes back when
  the story is ready.

## How to start it
Two ways, the same course (the `tf` skill):

| Way | Command | When |
|---|---|---|
| the `tf` agent | `claude --agent tf`, then the task (as below) | a session only for the automation |
| in any persona | `/tf <task> [--auto] [--budget USD]` or an ordinary sentence | once, in the current session |

**What you can give as the task** — the factory recognises what it is; you do not type the tool's name:

| You give | Example | What happens |
|---|---|---|
| an issue number | `/tf EBO-1236` | the factory reads the issue from Jira with a script (when it has credentials) or from a tracker connected in the session — read-only; without a connection it asks you to paste the content |
| an issue address | `/tf https://firma.atlassian.net/browse/EBO-1236` | it takes the tracker and the number from the address |
| a cut key from a change plan | `/tf TSK-57` | the cut's task `CHG-12-TSK-57` (pdi mode) |
| content or a file | `/tf As an operator I want…`, `/tf docs/story.md` | a task with the key `T-<date>-<name>` |
| the key of an existing task | `/tf EBO-1236` after a break | resuming from the first unfinished slice |
| nothing | `/tf` | the list of tasks in progress and a question about what next |

- **The tracker (Jira, Linear, GitHub…):** the factory uses the connection you added to Claude Code yourself (an MCP
  server); it installs nothing and changes nothing in the tracker. When several are connected, it asks once which one
  the issues come from and records the answer in `.tf/config/operations.json` (preview and change: `python3
  .claude/skills/tf/scripts/intake.py tracker`). Without a connection, pasting the issue's content is enough.
- **Jira without the model:** when the environment has the variables `JIRA_BASE_URL` and `JIRA_EMAIL` with
  `JIRA_API_TOKEN` (Jira Cloud) or `JIRA_TOKEN` (Data Center), a script fetches the issue: one read-only request, only
  over `https://`, without redirects. The factory does not store or print this data; it changes nothing in Jira.
  It takes the address only from the variable — not from a file in the repository, which someone else's pull request
  could change; when the operations card has a different Jira address than the variable, the script refuses. A check
  on your side: `python3 .claude/skills/tf/scripts/intake.py fetch EBO-1236`. The custom field with acceptance criteria
  you point to in the card: `"fields": {"acceptance": "customfield_10042"}`.
- **Where the content comes from:** the task's `ticket.md` starts with the line `Source: … · fetched: <date>`. For the factory the issue's content is data, not instructions — an instruction found in an issue you
  will see as a remark, not as an action taken.
- **Forcing the way of working:** `/tf task …` (alias `zadanie`), `/tf question …` (alias `pytanie`; an answer only),
  `/tf quick …` (alias `szybko`; a small change right away, without creating a task).

Options (in the message to the agent or with the command):
- no option (normal mode) — the factory shows the specification and the plan and waits for your consent; it records
  the consent and only then starts the code;
- `--plan` — only the specification and the plan, no code changes; you start delivery later with `/tf <KEY>`;
- `--auto` — the plan does not wait for your consent (except for full-weight tasks);
- `--budget <USD>` — a hard limit: after the slice that exceeds it, the loop stops. By default there is no budget,
  but the factory always chooses the cheapest sufficient model and the least work.

Example:
```
claude --agent tf
> As an operator I want to import a CDR file (CSV) and see the sessions with an error. --auto
```

## The task's weight
The factory itself assesses how much care the task needs and tells you in one sentence at the start:

| Weight | When | What it changes |
|---|---|---|
| light (`light`) | a typo, a name, a comment, documentation — without acceptance criteria, one slice | no specification and no flag; the test, the evidence and the scope review stay |
| normal (`normal`) | everything else | the full course described below |
| full (`full`) | login, passwords, permissions, payments, database migrations, personal data, secrets, deployment — in the task's content or in the plan's files | you approve the plan before the code is written; with `--auto` the factory stops and waits for your consent; the security review is mandatory |

- A script computes the weight from the task's content and the plan's paths, not the model. When the plan touches e.g.
  migrations, the weight rises by itself.
- Anyone (the factory too) can raise the weight. **Only you can lower it**, with a reason:
  `tf task weight <KEY> --set normal --by human:<your identifier> --reason "…"`. After your decision the factory
  no longer changes the weight.
- A preview of the weight with the reason: `tf task weight <KEY>`.

## What it does
1. **Start:** it needs a clean working tree, creates the run directory and the branch `story/<slug>`.
2. **Taking in the story:** it checks who, what and why, and the acceptance criteria. When they are missing, it asks up
   to 3 questions (with `--auto` — it stops with those questions).
3. **The plan:** up to 5 vertical slices — each carries value, passes the tests on its own and is a separate commit.
   A story for more slices → a proposed split and a STOP.
4. **Slice by slice:** a test that fails → the smallest code → verification (tests, lint, types) → a security
   scan (semgrep OWASP Top 10 on the slice's files, a dependency audit when the manifest changes) → a scope review by
   `scope-reviewer` in a fresh context → a commit. The reviewer marks every finding: **important** (to fix in this
   slice — only that starts a second round), **minor** or **pre-existing** (it was in the code before the change) —
   those two go to the postponed items. A slice has at most 2 rounds; the script refuses a third and the run ends with
   a STOP block describing the blocker, and after your decision it gets two more.
   **An option (off by default):** with `loop: {blocked_slices: true}` in `.tf/config/config.yaml` a question stops
   only the slice it concerns — meanwhile the factory does the slices that do not depend on it, and the question is
   visible on the "Waiting for you" list. `events.jsonl` in the task directory records the questions
   and answers.
5. **KISS:** edge cases, ideas and risks outside the criteria do not go into the code, only into `parked.md`
   and into the "Postponed for a decision" section of the PR description.
6. **Conditional phases:** documentation only when the public API changes, the security review only with auth,
   secrets, IaC or CI, the architect only for a decision that is hard to reverse.
7. **The end:** one PR (the factory does not merge it) and a report.

## When the factory stops
A stop (STOP) always has one of eleven reasons — the script accepts no other — and says what it needs from you:
missing information (`question`), a task to split (`split`), missing content of or access to the issue (`source`), the
plan waiting for approval (`plan-approval`), tests red after two attempts (`tests`), the security scan (`scan`), the
budget exceeded (`budget`), an unprepared repository (`environment`), a decision about a dependency (`dependency`),
a contract change or a business decision (`contract`), an operation reserved for you (`permissions`).

You get every stop in the same shape: **what happened**, **what is needed**, **one question** with 2–3
options (each with its consequence and one recommendation) and what the factory will do after your answer. The same is
visible in the preview in the "Waiting for the human" column. The messages' text is in
`.claude/skills/tf/templates/stop_messages.json`.

## What you get
Every story is a **task** with a key (`T-<date>-<slug>` or a number from the tracker: `start --key PROJ-123`) and two
directories:

| Where | What | Git |
|---|---|---|
| `docs/project/changes/<KEY>/` | `ticket.md` (the story), `spec.md` (AC-n criteria in the Given / When / Then form, what stays unchanged, what is out of scope, open questions — a script checks it; with errors there is no plan; the file is created only when the loop starts the specification), `plan.md` (slices to tick off — you resume an interrupted run from it), `task.json` (the state), `evidence/` (the slices' verification evidence), `report.md` (the report) | yes — with one commit `docs(task): record <KEY>` at the end of the run |
| `.tf/runs/<KEY>/` | `run.json`, `parked.md` (items postponed for your decision), scan results, full verification logs | no |

The list of tasks: `tf status` (computed live from the task folders); the state of one: `tf task status <KEY>`. A slice
is "done" only with evidence: the loop runs the verification through `run_state.py verify`, and without current evidence
the script will not tick the slice off and will not let the run through to the PR. The same without a recorded, passed
scope review (`run_state.py step … scope pass`): in the measurement after step G the loop always called the reviewer,
but recorded the result in 7 of 15 runs. After a review without important findings the loop finishes the slice with one
command `run_state.py done <directory> S<n> --message "<type>(<scope>): <description>"`: recording the review, committing the
evidence's files with footers, ticking off and the next slice. The quality gate does not react to changes in
`docs/project/changes/`.

A cut from a change plan (`/tf TSK-57`, pdi mode) is the same kind of task, with a key made of the change and the cut:
`docs/project/changes/CHG-12-TSK-57/` and `.tf/runs/CHG-12-TSK-57/`. The differences: the task's content comes from the
cut's row and the change's intent, the flag — from the release plan, the report also goes to
`docs/project/changes/CHG-12/runs/TSK-57.md` (pdi takes the PR description from there); `tf status` shows cuts
together with their change.

The report (`python3 .claude/skills/tf/scripts/run_report.py finish <directory>`): time, tokens (input, output, cache
read and write), the cost in USD, models and agents, slices done / planned, the number of postponed items. A script
computes it from the session transcripts, not the model, so it uses no tokens. The cost is an estimate from the API
price list — with a subscription an equivalent, not an invoice. During the run, one status line:
`python3 .claude/skills/tf/scripts/run_report.py status <directory>`.

A live preview: `python3 .claude/skills/tf/scripts/run_state.py dashboard` builds `.tf/runs/dashboard.html` (you open
the file in a browser, it refreshes itself every 5 s). The columns are the run's stages (Intake, Plan, Slices, PR,
Waiting for the human, Done), a card shows the rounds of the
current slice (R1, R2…) and the loop's steps (test, code, verify, scan, scope) and a bar of slices S1, S2… — a purple
slice was ticked off but has no current evidence (a file changed after the verification). A card also shows the task's
stage, and a task without a run (created with `tf task` alone, a fresh clone) has its own card. The file panel splits
files into the task directory (git), the working directory, evidence, the code files of every slice, scan results,
STOP and `report.md`. Above the board is the **"Waiting for you"** list: a plan to approve, a stopped
run (what happened, the question, options with a recommendation, since when it has been waiting) or a slice blocked by
a question. The same as text: `tf status` (the "waiting for you" line under the task); `tf status --open` builds the
preview and opens it in a browser at any moment. The loop records the state with the commands `run_state.py stage` and
`run_state.py step`; a script computes cost and time from the transcripts (`dashboard` without `--no-cost`).
`run_report.py start` builds the dashboard itself and opens it in a browser (a cut with a key, called by the pdi phase,
only builds it). You turn this off in `.claude/tf.json` (a personal file, a factory update does not touch it):
`{"dashboard": false}` — not at all, `{"dashboard_open": false}` — it builds but does not open; both are `true` by
default. The variables `TF_DASHBOARD=0` and `TF_DASHBOARD_OPEN=0` do the same.

Agreement of the changes with the plan (`python3 .claude/skills/tf/scripts/plan_drift.py <directory> --base main`):
changed files vs the slices' files, changes outside the plan, the plan's coverage of the diff and tests in the diff —
it goes into the PR description.

**A script, not the model, writes the PR description** (`python3 .claude/skills/tf/scripts/run_state.py pr-body
<directory> --base main` → the file `.tf/runs/<KEY>/pr-body.md`, passed with `gh pr create --body-file`). Every PR has
the same fields: the story, slices with commits, the criteria trace, **How it was checked** (the
command, the exit code and the evidence file of every slice, the security scan's verdict, agreement with the plan),
**System diff** (what the change touches beyond code lines: UI, data, API, dependencies, configuration, operations; `tf diff`), **Risk** (the task's weight and the `tf risk` triage), **How to roll back**, postponed items and
assumptions. A slice without green evidence is named plainly in the description. The script takes the deployment
rollback step from the operations card (`.tf/config/operations.json`, the `deploy.rollback` field — text or a list of
steps); without it, it gives `git revert` of the merge commit, and for a task with a flag it starts with turning the
flag off.

**After the merge.** The operations card has a deployment part (`deploy`), which `tf onboard` creates: `smoke` (the
smoke test command), `rollback` and `rollback_minutes` (how to roll back and how long it takes), `approval` (what the
human approves), `logs` (the logs command). After a deployment you run `tf task deployed <KEY> [--version X]`: the
factory runs the smoke test and records the result in the task (`evidence/deploy-<n>.json`). A green result moves the
task to the "deployment" stage. A red one ends with the question "roll back?" with the rollback step and the logs
command from the card, and the task is on the "waiting for you" list until you record a decision
(`tf task deployed <KEY> --rolled-back --by human:<id>`) or a repeated test after a fix is green. Without `smoke` in
the card the factory ends at the merge — the end of the run and the command itself say so. The factory deploys nothing
and rolls nothing back by itself.

**The reviewer panel at full weight.** A full-weight task (login, payments, permissions, migrations, secrets, personal
data) moves to the PR stage only after two reviews in separate contexts: `security-reviewer` (the change's security)
and `spec-reviewer` (every criterion and every "Unchanged" rule from the specification, with evidence).
`run_state.py panel <directory>` gives the composition and the commissions; the loop records the verdict
(`--record <reviewer> pass|fail`), and by hand: `tf task review <KEY> <reviewer> pass|fail --note "…"`. The verdict
concerns a commit — after a fix in a new commit the review starts again. Light and normal weights have no panel.

**Closing the task.** `tf task close <KEY>` closes the task when: the change is merged (the task file is on the
default branch — this also works with a squash merge), the deployment is not waiting for a rollback decision, and every
important finding of the review has a recorded control that will catch it next time. The loop records important
findings at the moment the scope review fails (`run_state.py finding`; without it, recording a failed review is
rejected); you add the control with `tf task finding <KEY> control F1 "<test, hook, rule or the reason it is missing>"`.
Closing reminds you about the flag's removal date. Only a human records a lesson for the future: `tf task close <KEY>
--lesson "**rule** — Context: … · Instead: … · Applies to: …" --by human:<id>` appends it once to
`docs/project/lessons.md`; the factory does not invent lessons by itself. When the merge cannot be confirmed (e.g. no
git), a human can close the task anyway: `--force --by human:<id>`. Closed tasks are not on the `tf status` list;
`tf status --all` shows them. If the project has a reconstruction from the code (`docs/project/00-reconstruction/`),
the loop reads the standards index and the domain glossary when taking in the story.

## Security and the version cooldown
After the slice's tests are green, the loop runs
`python3 .claude/skills/tf/scripts/security_scan.py scan --slice S<n> --attempt <k> --out <directory>/security/S<n>`:
semgrep with the `p/owasp-top-ten` rules (and the product's `.semgrep.yml`, if any) only on the changed files, `npm audit`
or `pip-audit` only when the manifest or the lockfile changes (`package.json` without dependencies and without a
lockfile — the audit skipped with a note in the report; with dependencies without a lockfile — a scan error); the result
of every attempt (SARIF, `verdict.json`, `summary.md`) is a separate directory `<directory>/security/S<n>/attempt-<k>/`, and
`<directory>/security/S<n>/feedback.md` holds the findings of the last attempt. The run report lists every attempt of the
slice (e.g. FAIL with findings, then PASS). A blocking finding (an error or a warning with a CWE from the OWASP Top 10 —
the same rule as SEC-001 in ci_for_sdlc) is a red gate: the second attempt gets the findings (the rule, file:line),
after two attempts a STOP and no commit. Findings below the threshold go to the "Security" section of
the report. A missing semgrep or pip-audit is a FAIL with an installation command (`pipx install semgrep`,
`pipx install pip-audit`), never a silent PASS.

Requirements for the product:
- **One verification command (N3):** a script in the style of `templates/verify.sh` (format, lint, types, tests, scan),
  named in the first line of the product's `CLAUDE.md`; the loop and CI run the same one (templates in mode-pdi).
- **A 7-day version cooldown (N10):** `.npmrc` `min-release-age=7` (npm ≥ 11.10), `pnpm-workspace.yaml`
  `minimumReleaseAge: 10080` (minutes, pnpm ≥ 10.17), `.yarnrc.yml` `npmMinimalAgeGate`, `[tool.uv]
  exclude-newer = "7 days"`; the lockfile in git. `security_scan.py cooldown` checks this at the start of the run. A
  pnpm caveat: Dependabot updates the lockfile without a cooldown, and `pnpm install --frozen-lockfile` in CI then ends
  with `ERR_PNPM_NO_MATURE_MATCHING_VERSION` (pnpm/pnpm#11203, #12450) — Dependabot PRs with versions younger than
  7 days wait or have a `cooldown` in `dependabot.yml`.
- **Network:** the semgrep rule registry is fetched from `semgrep.dev` — in a container with a list of allowed hosts
  add it (Z8a); without a network give local rules through `TF_SEMGREP_CONFIG=<file.yml or directory>`.
- **A registry without login:** `p/owasp-top-ten` is fetched without `semgrep login` (semgrep 1.183.0, checked
  2026-11-03: 560 rules), but the set is narrower than the full rules — it lacks e.g. `tainted-sql-string`
  (Express) and rules for `node:sqlite`. Patterns the registry does not catch the product adds in `.semgrep.yml`
  (the scan always includes it); logging in with a token (`SEMGREP_APP_TOKEN`) gives a wider set in CI.

## When the loop stops
The STOP block says what blocks it (with evidence), what is already done (commits), what it needs from you and from
which slice to resume. After your decision ask for a resume and give the run directory: the first unticked slice in
`plan.md` is where it continues. The cost report is written also after a STOP.

Details of the course: `.claude/skills/tf/SKILL.md` (in the factory's sources:
`core/skills/tf/SKILL.md`); the mechanism: `docs/insights.md` in the factory repository, the section
on modes.
