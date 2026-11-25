# The human's git questions: commit messages, push, PR, revert

You read this before the loop's first commit (`finish-slice` / `done` with `--message`), before pushing the branch and
opening the PR, and when the human answers "No" to the push. In the **normal** mode the human approves every commit
message, the push and the PR title with AskUserQuestion. In **Auto** (`--auto`) there are no questions.

## Who the author is
The author of every commit is the person logged into git (`user.name` / `user.email`), as is. No `--author`, no
`git -c user.name=…`, and no AI attribution in a message or PR body: no `Co-Authored-By` for an AI, no `Claude-Session`
link, no "Generated with Claude Code" line. `run_state.py` drops such lines if they slip into `--message`; the factory
settings (`attribution`) stop Claude Code from adding them. A human pair's `Co-Authored-By` stays.

## 1. The commit message: one question per commit
Before `run_state.py finish-slice … --message` (or `done`), one AskUserQuestion:
- question: "Commit message for S<n>?"
- option 1: your proposed Conventional Commit message, with "(Recommended)" in the label, the full message in the
  description;
- option 2: an alternative wording (a different verb or scope, not a different change);
- "Other" (always offered by the tool) lets the human type their own.

Pass the chosen text unchanged as `--message`. A light task has one slice, so one question. When the gate fails and you
call `finish-slice` again for the same slice, keep the approved message: no new question. The task-files commit that
`run_report.py finish` prints at the end holds only the task's records: no question, its message as printed.

## 2. Push and PR: one call, two questions
After `pr-body` and before the push, one AskUserQuestion call with two questions:
1. "Push branch `<branch>` to `<remote>`?" — "Yes, push (Recommended)" · "No, keep it local".
2. "PR title?" — your proposed title (Recommended) · an alternative wording; "Other" for their own. Say in the
   question text, in one line, what the body holds (from `pr-body.md`: slices, evidence, how to roll back).

"Yes" → `run_state.py push <katalog> --by human:<id>` (the id as for `approve`), then `gh pr create --title
"<chosen title>" --body-file <file>`. The script pushes the task branch recorded in run.json with `-u`, never forced,
and checks the autonomy policy itself, so the human's answer is the only confirmation: no second permission window.
You do not run a raw `git push`: outside this command `guard_bash` asks again (its safety net).

## 3. "No, keep it local" → the revert question
Ask once more, with AskUserQuestion:
- question: "Revert all changes the factory made for <KEY> and return to the state before /tf-task started?"
- "Keep the work locally (Recommended)" — nothing changes: say the branch (`<branch>`, `git switch <branch>`), then
  the task-files commit and `run_report.py finish` as usual, with no PR.
- "Revert everything for <KEY>" — `run_state.py revert <katalog> --by human:<id>` (the id as for `approve`: the
  human's git user name). Show its output; it ends with the undo commands. Do not run `run_report.py finish` after it:
  the run directory is archived.

What `revert` does (deterministic, refuses rather than guesses):
- returns to the base branch recorded by `run_report.py start` (its current state, never `git reset --hard`);
- deletes the task branch only when it was never pushed; a pushed branch is kept and the output says so;
- moves `docs/project/changes/<KEY>/` and `.tf/runs/<KEY>/` to `.tf/backup/revert-<KEY>-<date>/`;
- refuses when there are uncommitted changes that are not the task's (it lists them), for a run without a recorded base,
  and without `--by human:<id>`; it never touches the human's stash or `git clean`s anything.
It is a human decision: you run it only after the human chose "Revert everything" in this question.

## 4. Auto mode
No questions. Commit messages and the PR title as you propose them. The push follows the autonomy policy
(`autonomy.operations.git_push` in `.tf/factory/config.yaml`, tightened in `.tf/config/config.yaml`): call
`run_state.py push <katalog>` without `--by`; with `confirm` (the default) or `deny` it refuses, because nobody
answered, and prints the STOP `permissions` command: record it, the human pushes. You never run `revert` in Auto.

## Example
```
AskUserQuestion: "Commit message for S1?"
  · feat(pay): add card payment for long stays (Recommended)
  · feat(parking): charge 45 PLN by card after 12 hours
AskUserQuestion (two questions):
  "Push branch story/card-payment to origin?"  · Yes, push (Recommended) · No, keep it local
  "PR title? The body: 2 slices with evidence, trace AC-1..AC-2, how to roll back."
     · feat(pay): card payment for long stays (Recommended) · feat(parking): pay by card
```
