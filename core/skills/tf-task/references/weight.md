# The task's weight in the /tf-task loop

You read this when `run_report.py start` or the `plan` stage prints a line with a weight other than normal, when the script refuses a stage
because of the weight or when the human wants to change it. The script chooses the weight, not you and not the human: from the issue's content
at the start and from the plan's paths at the `plan` stage. You tell the human in one sentence what was chosen and why
("The change concerns passwords, so I'll show you the plan before the code").

| Weight | When | What changes in the run |
|---|---|---|
| `light` (lekka) | a typo, a name, a comment, documentation; no acceptance criteria; one slice, at most 2 files | without `spec.md` (so without a flag and a criteria trace); one slice; the test, `verify` evidence, the scan and the scope review stay |
| `normal` (zwykła) | everything else | the full run from SKILL.md |
| `full` (pełna) | login, passwords, permissions, payments, database migrations, personal data, secrets, deployment — in the issue's content or in the plan's paths | like normal, plus the two points below |

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

## Changing the weight
- A preview with the reason: `run_state.py weight <katalog>`.
- **Anyone can raise it**, also you, when you see a risk the script did not catch:
  `run_state.py weight <katalog> --set full`.
- **Only the human can lower it**, with a reason: `python3 .tf/factory/tf.py task weight <KEY> --set normal --by human:<id>
  --reason "<dlaczego>"`. When you think the weight is too high, you tell the human and give them this command —
  you do not run it yourself. After the human's decision the script no longer changes the weight.
- The light weight, and the plan came out at more than one slice → you raise it to normal and create a specification.
- A pdi slice has its weight computed from the slice's row (the intent of the whole change does not raise it). At the full weight an
  `--auto` run does not stop for consent: the human approved the change plan at the pdi gate. The `security-reviewer` review stays.
