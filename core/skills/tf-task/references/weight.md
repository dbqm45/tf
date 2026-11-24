# The task's weight in the /tf-task loop

> **Contents:** Your approach: a judgement, recorded once at the plan stage · The full weight · The mode proposal · Changing the weight

You read this when `run_report.py start` or the `plan` stage prints a line with a weight other than normal, when the script refuses a stage
because of the weight or when the human wants to change it. The script proposes the weight from the issue's content at the
start and from the plan's paths at the `plan` stage; your recorded approach (below) refines it within the script's floors. You tell the human in one sentence what was chosen and why
("The change concerns passwords, so I'll show you the plan before the code").

| Weight | When | What changes in the run |
|---|---|---|
| `light` (lekka) | a typo, a name, a comment, documentation; no acceptance criteria; one slice, at most 2 files | without `spec.md` (so without a flag and a criteria trace); one slice; the test, `verify` evidence, the scan and the scope review stay |
| `quick` (the fast lane) | your approach judges the change small and mechanical (no sensitive area; at most 1 slice and 15 files) | the fast lane below |
| `normal` (zwykła) | everything else | the full run from SKILL.md |
| `full` (pełna) | login, passwords, permissions, payments, database migrations, personal data, secrets, deployment — in the issue's content or in the plan's paths | like normal, plus the two points below |

## Your approach: a judgement, recorded once at the plan stage
The script proposes a weight from the ticket and the plan's paths (light / normal / full); **how to do the task is your
judgement**. After writing `plan.md`, before `stage plan`, record it with the evidence:

`run_state.py approach <katalog> --weight <quick|light|normal|full> --slices <n and why> --test-strategy "<…>"
--verify-scope "<the command or: full>" --review "<cheap, the diff only | full>" --rationale "<1–3 sentences: the files
touched, the nature of the change, the risk, the unknowns>"`

`stage plan` prints the `Approach:` line — put it into the plan question, so the human sees it and can override it in one
answer (an override: `… approach … --by human:<id>`).

Examples of the judgement (not rules):
- **Simple** — the same label or CSS class change in 8 templates plus one shared component: `quick`, 1 slice ("the same
  edit in many places"), one parametrized test per acceptance criterion, verification of only the touched spec files,
  a cheap diff-only review.
- **Middle** — a new field through a controller, a service and a repository with existing patterns: `normal`, a spec,
  2–3 vertical slices, a unit test per behaviour, `related` per slice.
- **Complex** — new domain logic across modules, an unclear rule, a contract change: `normal` or `full`, a spec with
  open questions answered first, several slices, unit and integration tests, the full suite before the PR.

### What the script enforces (floors only)
- A sensitive area (login, passwords, permissions, payments, migrations, personal data, secrets, deployment — in the
  ticket or the plan's paths) → anything below `full` is refused, with the reason.
- A plan larger than the weight allows (`quick`: 1 slice, at most 15 files; `light`: 1 slice, 2 files) → refused:
  re-assess (a heavier weight or a smaller plan).
- A lower weight once the loop has started, or below a human's decision → only with the human's OK (`--by human:<id>`).
Nothing else is decided by a script.

### Escalation during the loop
When the work turns out bigger — unexpected failing tests, files outside the plan, a new unknown — escalate at once and go on
under the heavier rules: `run_state.py approach <katalog> --weight <normal|full> --rationale "escalated: <what you found>"`
(normal and full need `spec.md`: create it before the next stage). The escalation goes into the run report. Going back down
mid-run only with the human's OK.

### The fast lane (`quick`) in practice
1. **No `spec.md`:** the ticket's criteria are enough (no flag decision, no criteria trace).
2. **One slice:** the same change in many places is one slice.
3. **Tests:** one test per acceptance criterion (`AC1` in its name), parametrized over the places where possible — not
   one per component. Check the cheapest observable thing (the shared component's class, the constant's value); not
   regular expressions over templates when a cheaper check exists. TDD stays: the test is red first.
4. **Verification:** `related` for the slice's files, or `--command` with the narrowest command that runs only the touched
   test files (`finish-slice` warns when it would run the whole suite). `--full` before the PR only when the approach says so.
5. **The scope review stays, capped:** `scope-reviewer` on the cheapest tier (the Agent tool's `model: haiku`), the
   `git diff` only, no exploration. No answer within `loop.scope_review_minutes` (default 5) → `finish-slice …
   --review incomplete`; the PR description says "scope review: not completed".
6. **The scan** runs as always on the slice's changed files; only the project's recorded decision about a missing scanner
   changes it (`references/security.md`).
7. **The visual check** is not run by default: `ui_snap.py worth` says `ask at the end` — one question after the slice.
8. **The plan approval** stays in the normal mode, as one short question with the `Approach:` line.

## The full weight
1. **The human approves the plan before the code.** After saving the plan: `run_state.py stage <katalog> needs --needs plan`,
   you show the plan and wait. After the human's consent you record it: `python3 .tf/factory/tf.py task approve <KEY>
   plan.md --by human:<id>` (the identifier of the human who agreed) — only then does `step` let the slice loop in.
   **With `--auto` there is nobody to ask:** you end with a STOP block ("a task with the full weight — the plan waits for your consent"),
   with the plan in the report. You do not record the consent yourself.
2. **The script guards the reviewer panel before the PR.** `run_state.py panel <katalog>` gives the composition and the commissions:
   `security-reviewer` (the diff's security) and `spec-reviewer` (every `AC-n` criterion and every "Unchanged" rule
   from `spec.md`, with file:line evidence) — each in a separate context, through the Agent tool. You record the verdict:
   `run_state.py panel <katalog> --record <recenzent> pass|fail --note "<najważniejsze ustalenie>"`. The `pr` stage passes
   only with a `pass` from both for the current commit; after a fix in a new commit the review starts again. `architect` — when the plan
   contains a decision that is hard to reverse (a data migration, a contract change).

## The mode proposal
At the `intake` and `plan` stages `run_state.py` prints a `Mode:` line: the factory's proposal of how much autonomy
the task gets (`tf task mode <KEY> --propose`), computed by a script from the task's content and its weight, never by you:

| Content and weight | Proposal |
|---|---|
| one short sentence, no criteria (neither in the ticket nor as `AC-n` in `spec.md`) | `plan` — only the specification and the plan |
| no acceptance criteria, an open question ("TBD", "do ustalenia", "(SMS czy push?)"), a placeholder, a performance task, or the full weight | `normal` — the plan waits for the human |
| a small mechanical change (a typo, a rename, documentation) or the light weight, without gaps | `auto` |
| the fast lane (`quick`) | `normal` — one short consent to the plan |
| a clear task that changes behaviour | `normal` |

Always within `task.allowed_modes`. What the line asks you to do:
- **"lowered to …"** — the factory took a more cautious mode itself (a default from the style, not the human's choice):
  tell the human in one sentence.
- **"proposal …, Ask the human"** — a more autonomous mode is possible: AskUserQuestion with the proposal first; record
  only the human's answer (`tf task mode <KEY> <mode>`). You never raise the mode yourself.
- **"chosen by the human"** — the human's mode stays; name the factory's doubt in one sentence.
- A pdi cut keeps the mode approved at the gate.

## Changing the weight
- A preview with the reason: `run_state.py weight <katalog>`.
- **Anyone can raise it**, also you, when you see a risk the script did not catch:
  `run_state.py weight <katalog> --set full`.
- **Only the human can lower it**, with a reason: `python3 .tf/factory/tf.py task weight <KEY> --set normal --by human:<id>
  --reason "<dlaczego>"`. When you think the weight is too high, you tell the human and give them this command —
  you do not run it yourself. After the human's decision the script no longer changes the weight.
- The light weight, and the plan came out at more than one slice → you raise it (`approach`) and create a specification.
- Your recorded approach sets the weight at the plan stage, below the script's proposal too, within the floors above;
  `weight --apply` then keeps it, unless a sensitive area raises it to full.
- A pdi slice has its weight computed from the slice's row (the intent of the whole change does not raise it). At the full weight an
  `--auto` run does not stop for consent: the human approved the change plan at the pdi gate. The `security-reviewer` review stays.
