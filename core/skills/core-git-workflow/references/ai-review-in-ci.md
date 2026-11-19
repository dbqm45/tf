# PR review by AI in CI — an operational pattern

Review criteria against the plan and triage with the human: the change review skill (pack-it: qa-change-review).
Workflow security (permissions, action SHAs, `env:` instead of interpolation): the CI/CD skill (pack-it: ops-ci-cd). This file describes how an AI review works **as a CI step**.

## 1. When to run it
- On an event that means something: a PR opened and updated — not "every hour just in case".
- A label (e.g. `ai-review`) or a path filter, so a PR with documentation alone does not pay for a review.
- **Triage before the review:** a cheap step (the number and paths of files, the diff size, labels) gives the PR a risk level.
  Low → a fast, cheap run; critical paths (auth, payments, migrations, `infra/`, `.github/`) → a stronger
  model and always a human. Record the level, so you can count the cost per level (core-cost-control).
- A PR from a fork: the job does not run (the condition `github.event.pull_request.head.repo.full_name == github.repository`),
  because it must not be given secrets or write rights (core-agent-security).

## 2. The agent's input
- The diff against the base with three dots (`git diff origin/<baza>...HEAD` — only the PR's changes). It needs
  `actions/checkout` with `fetch-depth: 0`; with a shallow clone the diff is empty, and the agent "approves" nothing.
- The PR title and description through `env:`, never through `${{ … }}` in `run:`.
- Filter lockfiles, generated code and dumps out of the diff — cost and noise.
- A review against the plan: the plan is pointed to by a convention (the step report file changed in the PR) with an override by the line
  `Plan: <ścieżka>` in the PR description. **No plan = a neutral comment and exit code 0**, not a red check.

## 3. The output contract
- A report in a fixed shape: a fixed marker at the start (e.g. `<!-- AI-REVIEW-REPORT -->`) and the line
  `- **Werdykt**: …`. The next workflow step checks the marker and the verdict deterministically. A model that
  "improvises the format" is to turn a check red, not pass silently.
- Instead of parsing text you can force JSON: `claude-code-action` with `--json-schema` in `claude_args` returns the result
  in the step output `structured_output` (read with `fromJSON(steps.<id>.outputs.structured_output).verdict`).
- A three-level verdict:
  - **APPROVED** — all dimensions passed or at most 2 minor warnings;
  - **NEEDS_ATTENTION** — a few warnings or one non-critical failure; a green status with the description "for triage";
  - **REJECTED** — a security gap, a big drift from the plan, a threat to data, failing or missing promised tests.
- The agent in CI does not send a formal "approve" or "request changes" — only comments. The human decides.

## 4. Findings
The format, weight (critical / warning / observation), impact (low / medium / high), the limit of 10 findings and the rule
of one fix — as in the change review skill (pack-it: qa-change-review, "Finding"). In CI additionally: a secret found in the code you describe without
the value (`<UKRYTE: token pasujący do wzorca X>`), because everyone with access to the repo reads a PR comment.

## 5. Dimensions in a review against the plan
From the plan extract: the files from the phases, the automatic verification commands, the manual criteria, "Out of scope", the key decisions.
| Dimension | Failed when | Warning when |
|---|---|---|
| Agreement with the plan | a planned change is missing from the diff; a big drift of meaning | a small drift |
| Scope discipline | changes contradicting "Out of scope" | harmless additions (a helper for planned code) |
| Security and quality | any critical finding | only warnings |
| Architecture | broken module boundaries or dependency direction | — |
| Consistency with neighbouring code | rarely (when something breaks) | a significant deviation from 1–2 similar files |
| Tests | a test promised in the plan does not exist or fails | new behaviour without a test, a shallow test |
| Success criteria | the lint, build or typecheck from the plan fails | a manual criterion ticked without a trace in the code |
The plan defines what "tested" means; you do not judge what the plan did not promise.

## 6. Publishing and the gate
- **The gate lives in the workflow, not in the agent.** The agent's step ends with exit code 0 even at REJECTED; the next step
  (`if: always()`) reads the verdict and sets a commit status with a fixed context (e.g. `ai-review/verdict`), which
  later runs overwrite. Branch protection requires this status. When the agent fails, the comments stay.
- **A deliberate bypass:** a label (e.g. `ai-review-override`) added by a human changes the status to green
  with the description "bypass". The `labeled`/`unlabeled` events run only the cheap verdict step, without a new review.
- **A commit of the report by a bot** (when the report is to live in the repo):
  - a subject with `[skip ci]`, checked before the push (`git log -1 --format=%s | grep -F '[skip ci]'`, otherwise abort) —
    without the marker the workflow runs on its own commit in a loop;
  - always a new commit, never `--amend` (the history of reviews = an audit trail);
  - after a commit with `[skip ci]` the check hangs on the old SHA — you set the status explicitly on the bot commit's SHA.
- **A guard step at the start:** the last commit authored by the bot or with `[skip ci]` → skip the review.
- **Inline comments only on lines added in the diff** (`+` hunks) — check it deterministically before sending.
  Send the comments one by one, so a position error is loud; findings without a line in the diff go to the summary
  comment. [unverified: creating a review in bulk through the API is said by the course to silently drop comments
  with a wrong position — check in the GitHub REST documentation before relying on it]
- **Deduplication:** every bot comment ends with a hidden marker; first you publish the new ones, then you delete the old ones
  with the marker and a date from before the run started. When the new ones did not go out, the old ones stay — never zero information.
- The summary comment: the verdict, the dimension table, a link to the report (`blob/<SHA>/<ścieżka>`), at most 5 findings
  one line each.
- `claude-code-action`: limits and tools you give in `claude_args` (e.g. `--model`, `--max-turns`, `--allowedTools`);
  you pin the action to the full SHA. A ready workflow from this pattern: `scripts/ai_review.py install` (the template
  `templates/ai-review.yml`: the verdict from JSON, the status, the summary comment with deduplication, a bypass by label); a skeleton
  for your own changes (pack-it): `.claude/skills/ops-ci-cd/references/examples.md`, example 4.

## 7. The learning loop
Every month: where the human only rubber-stamped the AI verdict (wasted attention → the triage can be loosened), and where a bug
got through a green review (a gap in the criteria → a new case in the evaluation set and a `REVIEW.md` fix).
Evaluating the review prompt: `.claude/skills/core-delivery-lifecycle/references/ai-native-sdlc.md` §5. The cost and time per PR and per
triage level on a shared dashboard.

## 8. Splitting the review skill
Keep the assessment criteria (what to compare, how to assess, the shape of findings) in a separate file independent of the tool,
and the mechanics (where the diff comes from, where the result goes, how to comment) — in the skill or the workflow. The same criteria file is then read by
`claude-code-action`, your own agent on the SDK and a human as a checklist.

Sources: the 10xDevs course, ed. 3 (2026), module 5, lesson 3 (AI review in CI) — training material (accessed 2026-10-09);
`anthropics/claude-code-action`, `action.yml` on the `main` branch (the inputs `claude_args`, `classify_inline_comments`,
the output `structured_output`; accessed 2026-10-10). Described in our own words.
