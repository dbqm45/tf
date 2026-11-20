# Work modes and stops in the /tf loop

You read this when the human gave `--plan` or `--auto`, when the script refuses entry into the slice loop ("the human's consent to
the plan", "Plan mode"), when you end with a STOP block and have to choose a code, or when the script rejects a STOP with the `question` code
and tells you to block one slice.

## Modes
The human chooses the mode in the command; you only record it at the first `run_state.py stage <katalog> intake`
(`--plan` or `--auto`; without an option — the normal mode). You do not change the mode yourself to get around consent.

| Mode | The human's command | What you do after the plan |
|---|---|---|
| Plan | `/tf <zadanie> --plan` | you end: `run_state.py stage <katalog> needs --needs plan`, you show the specification and the plan, then `run_report.py finish` and a commit of the task's files. You do not touch the code. |
| normal | `/tf <zadanie>` | `run_state.py stage <katalog> needs --needs plan`, you show the specification and the plan and wait. After the human's consent: `run_state.py approve <katalog>` — only then does `step` let the slice loop in. One consent covers the plan and the specification. |
| Auto | `/tf <zadanie> --auto` | you go on without consent; the plan and the assumptions go into the PR description. At the full weight the Auto mode does not work — the normal one stays (`references/weight.md`). |

- **Resuming after the Plan mode:** the human writes `/tf <KLUCZ>`; you change the mode to the one from the command
  (`run_state.py mode <katalog> normal` or `auto`) and go from the consent to the plan.
- `run_state.py approve` records the consent with the human's identifier from git. You call it only after the human's explicit consent
  in the conversation ("yes", "I accept the plan"); in the Auto mode the script refuses, because there is nobody to ask.
- A change of the plan or the specification after consent needs a new consent; ticking slices does not invalidate it.
- A preview of the mode: `run_state.py mode <katalog>`.

## Stop codes
You always record a STOP block with a code from this list:
`run_state.py stage <katalog> needs --needs stop --code <kod> --reason "<powód z dowodem>"`. A code outside the list or
no code is a command error. You choose the code that says **what is needed from the human**:

| Code | When | What is needed from the human |
|---|---|---|
| `question` | acceptance criteria are missing or an answer to a `[blocking]` question | answers to the questions (up to 3, specific) |
| `split` | more than 5 slices or several actions in one story (STORY-001) | choosing a split from your proposal |
| `source` | there is no task content or no access to the issue | pasting the content or a connection to the tracker |
| `plan-approval` | the full weight in a run with `--auto`; the plan waits for consent | consent to the plan or remarks |
| `tests` | verification red after two repair attempts | a decision: another way, a criterion change or stopping |
| `scan` | the security scan blocks after two attempts | a decision about the scan finding (a fix, an exception with a rationale) |
| `budget` | the cost above `--budget` | consent to further cost or ending |
| `environment` | uncommitted changes, no remote repository, no scanner or tool | preparing the repository or the tool |
| `dependency` | a new dependency, the version cooldown (a package younger than 7 days), no cooldown settings | a decision about the dependency or adding the setting |
| `contract` | a change of the public API, the data schema, a migration or a business decision that is not in the task | a decision; you do not choose the conservative option yourself |
| `permissions` | an operation reserved for the human: production, publishing, a flag outside the test environment, merging a PR | performing the operation or explicit consent |

"It's too hard" is not a code: you stop on evidence (a command and its output), not on your own assessment of difficulty.

## A question about one slice (the `loop.blocked_slices` switch)
It works only when the project turned the switch on in `.tf/config/config.yaml`; it is off by default and every
question is a STOP block. With the switch on, a question stops its slice, not the whole run:

- **The plan records dependencies** in the slice's line: `· after: S1` (can start after S1), `· after: none` (independent); without
  a note the slice depends on the previous one. The `plan` stage reminds about this.
- **A question during a slice:** `run_state.py block <katalog> S2 --question "<pytanie do człowieka>"`. The script
  answers `Next: S3` (do this slice) or `Next: STOP` with a list of questions and a ready stop command. A STOP
  with the `question` code for the current slice the script rejects while an independent slice is left.
- **A question about the whole task** (without an answer no slice can be done): STOP as usual, with `--task`.
- **After the human's answer:** `run_state.py answer <katalog> S2 "<odpowiedź>" --by human:<id>` — the slice goes back to
  the plan, and the script says what next. You do not record the answer for the human. Which slice now: `run_state.py next
  <katalog>`.
- A blocked slice has no evidence, so the `pr` stage will not pass while the question waits — the run then ends
  with a STOP block with the questions, and the done slices stay in the commits.

## What you show the human
After recording a stop the script prints **Komunikat dla człowieka** (a message for the human): what happened, what is needed, one question
with 2–3 options (each with its effect, one recommended) and what the factory will do after the answer. You show this message
instead of your own description — without words from the factory's internals (slice, gate, tier, hook) and without pointing to files to
understand the question:
- you complete it with something concrete from this run: evidence (a command and its output), questions for the human or a proposed split;
- in the conversation you ask the question with the AskUserQuestion tool: 2–4 options from the script, the recommended one first with
  "(Recommended)" in the label, a short consequence in each option's description (the tool adds "Other" for the human's own answer); the answer
  "decide yourself" you accept only when the decision is reversible and does not block the work;
- in an unsupervised run (`--auto`) the message goes to the report and to the answer ending the run;
- a preview of the message without recording a stop: `run_state.py message <kod>`.

## The preview and postponed items
- `start` opens the dashboard and prints a `Dashboard: …` line; when it is turned off in `.claude/tf.json`, there is no line and
  you do not mention the dashboard.
- A refusal of `stage`, `step`, `done` or `verify` names its cause (specification errors, missing evidence, a plan older
  than the specification) — you remove it and repeat the command.
- `parked.md` is outside git: in commits and code you do not refer to it; its items go into the PR description and the report
  (the "Postponed for a decision" section).
