# A feature flag per story

You read this at the plan (§2 of SKILL.md), when `run_state.py flag <katalog> mode` returns `auto`. A pdi slice run has
the flag from the release plan — see `.claude/skills/tf-task/references/pdi-cuts.md`.

## The decision (without it the `pr` stage is rejected)
| Change | What you record |
|---|---|
| new behaviour visible to the user | `run_state.py flag <katalog> set <klucz> --remove-by <RRRR-MM-DD>` |
| a bug fix, a refactoring, documentation, configuration or a project without a flag mechanism | `run_state.py flag <katalog> none --reason "bez flagi, bo …"` |

**The flag's name:** you ask the human, giving a proposal based on the task key (e.g. `proj_123_eksport_csv`). With `--auto` there is
nobody to ask — you take the proposal and record it in the plan and the PR description as
**[assumption: the flag name to be confirmed]**.

The result `manual` (the human turned off automatic flags, `feature_flags.auto: false`): you do not create a flag and record nothing
about it; in the PR description you write "the flag is added by the human".

## How you run slices with a flag
- the first slice creates the flag; every slice hides its behaviour behind it;
- the tests go in both states: on — the `AC-n` criteria; off — the old behaviour unchanged;
- the commits have the footer `Flag: <klucz>`;
- the last commit turns the flag on **only in the test environment** (the file and the environments: `.tf/config/operations.json`).

You do not turn the flag on in another environment and do not record consent for it (`tf task flag <KEY> allow …`) — that is the human's
decision. The check: `tf flag check <KEY>`; turning it on outside the test environment without recorded consent rejects the `pr` stage.
