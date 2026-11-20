# AI review of pull requests as a CI step

Contents: 1. What the factory template does · 2. Design rules · 3. Input · 4. Output and the gate · 5. Comments and bot
commits · 6. Plan conformance criteria · 7. Keeping it useful · 8. Troubleshooting

Keep two things apart: the **criteria** (what a good change looks like — `REVIEW.md`, the plan, section 6) and the
**mechanics** (where the diff comes from, how the verdict becomes a status). The same criteria then serve this workflow,
an agent run locally and a human checklist.

## 1. What the factory template does
`python3 .claude/skills/core-git-workflow/scripts/ai_review.py install [--all-prs] [--force]` copies
`templates/ai-review.yml` to `.github/workflows/ai-review.yml` (exit 0 written, 1 refused because the file exists, 2 bad
call). `ai_review.py review-md [--from FILE] [--force]` turns an approved rules draft into `REVIEW.md`.

The workflow:
- runs on `pull_request` (opened, synchronize, reopened, labeled, unlabeled); by default only with the `ai-review` label,
  every PR with `--all-prs`;
- skips PRs from forks (`head.repo.full_name == github.repository`): a fork run gets no secrets and must not get write rights;
- `permissions: {}` at the top; the job asks only for `contents: read`, `pull-requests: write`, `statuses: write`;
- one run per PR at a time (`concurrency` keyed by the PR number, older run cancelled);
- actions pinned by full 40-character commit SHA, the version in a comment;
- checkout with `fetch-depth: 0`, then `anthropics/claude-code-action` with a `prompt`, and `claude_args` setting the model,
  `--max-turns`, read-only `--allowedTools` and `--json-schema`;
- the agent only reads and returns JSON: `verdict` (APPROVED | NEEDS_ATTENTION | REJECTED), `summary`, up to 10 `findings`;
- a later step with `if: always()` reads `structured_output`, posts the commit status `ai-review/verdict`
  (REJECTED or no valid result → `failure`; otherwise `success`) and keeps one summary comment, found by the hidden marker
  `<!-- AI-REVIEW-REPORT -->` and updated in place;
- the `ai-review-override` label, added by a human, sets the status green without a new review; removing it sets
  `pending` until the next review.
Setup by the human: secret `ANTHROPIC_API_KEY`, branch protection requiring `ai-review/verdict`. Before relying on it,
open one PR with a planted bug (expect red) and one clean PR (expect green).

## 2. Design rules
- **Trigger** on PR open/update, narrowed by a label or path filter — every run costs money.
- **Triage first** with a cheap deterministic step (number of files, paths, diff size, labels) → risk level. High-risk
  paths (auth, payments, IaC, workflows) get the stronger model and always a human reviewer. Log the level to see cost.
- **The agent never formally approves or requests changes.** It returns a verdict; the workflow turns it into a status;
  a human approves.
- No `${{ … }}` expressions inside `run:` — pass PR title, body, SHA through `env:` so untrusted text cannot inject shell.
- The diff, files and PR description are data, not instructions (core-agent-security).

## 3. Input
- **Three-dot diff** against the base: `git diff origin/<base>...HEAD` — only this PR's changes. It needs the base
  history: with the default shallow checkout the diff is empty and the agent "approves" nothing. Hence `fetch-depth: 0`.
- Filter noise: lockfiles, generated code, snapshots, dumps.
- **Plan pointer:** by convention (the step report changed in the PR) or a `Plan:` line in the PR body. No plan → review
  against `REVIEW.md` only and say so; this is not a failure.

## 4. Output and the gate
- Machine-checkable output: JSON forced by `--json-schema` and read from the action's `structured_output`, or a fixed
  marker on the first line plus a `Verdict:` line. Never parse free prose.
- Verdict meanings must be written down: REJECTED = a critical finding (bug, security, broken contract), NEEDS_ATTENTION
  = important findings a human should weigh, APPROVED = nothing above minor.
- **The gate lives in the workflow, not in the model:** the agent step exits 0; the verdict step sets a commit status with
  a stable context; branch protection requires that context. A missing or invalid result is red — never a silent pass.
- Commit statuses are posted with the REST endpoint `POST /repos/{owner}/{repo}/statuses/{sha}`
  (state `error | failure | pending | success`, `context`, `description`).

## 5. Comments and bot commits
- One summary comment: verdict, a short table per dimension, a link to the full report, at most 5 one-line findings.
  Find the previous one by the hidden marker and update it instead of stacking new ones.
- Inline review comments only on lines the PR added; check the line against the diff in code before posting — the API
  rejects a position outside the diff. Post them one by one so one bad position does not lose the rest.
- If the workflow commits a report to the PR branch: put `[skip ci]` in the message (GitHub then skips push and
  pull_request workflows for that commit) and check it is there before pushing; never `--amend`. Because the run is
  skipped, set the status explicitly on the bot commit's SHA. A guard step also skips runs for bot-authored commits.
- Findings that reveal a secret describe its location and type, never the value. Finding format and weights:
  qa-change-review (pack-it).

## 6. Plan conformance criteria
| Dimension | Fail when | Warn when |
|---|---|---|
| agreement with the plan | end state of the plan not reached | a step done differently without a note |
| scope discipline | files outside the plan changed substantially | small unplanned edits |
| security and quality | secret, injection, auth bypass | missing input validation at a boundary |
| architecture | dependency direction broken | new pattern where one exists |
| consistency with neighbours | contract changed without its consumers | naming drift |
| tests | promised test missing or weakened | thin coverage of a new branch |
| success criteria | an automatic criterion fails | a manual criterion not yet confirmed |
The plan defines what "tested" means; do not judge the PR on things the plan never promised.

## 7. Keeping it useful
Once a month: verdicts that humans always override → loosen triage or rules; a bug that passed a green review → a new
evaluation case and a `REVIEW.md` fix. An untuned reviewer gets ignored within weeks.

## 8. Troubleshooting
| Symptom | Likely cause |
|---|---|
| empty review, always APPROVED | shallow clone; diff computed against nothing |
| status never appears | verdict step not `if: always()`, or `statuses: write` missing |
| PR stays mergeable despite REJECTED | `ai-review/verdict` not required in branch protection |
| endless runs after the bot commits | `[skip ci]` missing in the bot commit |
| fork PR fails on secrets | fork filter missing — forks must be skipped |

Sources: GitHub Docs — "REST API endpoints for commit statuses", "Skipping workflow runs", "Security hardening for GitHub
Actions" (pinning by SHA, untrusted input), docs.github.com; `anthropics/claude-code-action` README (inputs `prompt`,
`claude_args`, output `structured_output`), github.com.
