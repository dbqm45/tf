# Merge strategies and a PR stack

The `gh` (GitHub CLI) commands are an example. Other platforms have equivalents: changing a PR's target branch and merging
with a choice of strategy.

## 1. Merge strategy
| Strategy | What goes into the main branch | When |
|---|---|---|
| **squash** | one commit from the whole PR | by default for small PRs; a "one PR = one commit" history, an easy revert |
| **rebase** | the PR's commits one after another, without a merge commit | the PR's commits are carefully split and each one passes the tests |
| **merge commit** | the PR's commits plus a merge commit | long-lived branches or when the record of when and what was merged matters (e.g. a release branch) |

- One strategy applies in the repository (a repository setting or branch protection). Do not change it for
  a single PR without a reason.
- With squash give the commit title explicitly, that is the PR title with its number, e.g.
  `gh pr merge 42 --squash --subject "feat(api): limit zapytań (#42)"`. Without it the tool may take the branch name
  or the first commit. The title format is described in core-conventional-commits.
- The PR's state before merging: `gh pr checks <N>` (CI), `gh pr status` (your PRs and review requests),
  `gh pr view <N>` (description, reviews). You merge only with green CI and the required approvals.

## 2. A PR stack (stacked PRs)
A big change split into successive PRs, each of which targets the previous one's branch:
`main ← #1 (feat-a) ← #2 (feat-b, baza feat-a) ← #3 (feat-c, baza feat-b)`. Each PR is small and reviewed
separately, and the next ones can be created before the first one is merged.

**The problem after a squash:** after #1 is merged with a squash, `main` has one new commit that is not in the history
of `feat-b`. PR #2 still contains the original commits of #1, so the diff against `main` is too big, and moving it with
a plain `rebase` gives conflicts with your own, already merged change.

**The procedure** (in order, one PR at a time):
1. Merge the first PR (squash, the title explicitly) and fetch `main`: `git fetch origin main`.
2. Move the next PR onto `main` without the previous branch's commits:
   `git rebase --onto origin/main feat-a feat-b`. The command takes the commits that are in `feat-b` and not
   in `feat-a`, and replays them on `origin/main`. Only the changes of #2 stay.
3. Push the rewritten branch: `git push --force-with-lease origin feat-b`. This rewrites history, so only on
   your own branch and with the human's consent (the "Forbidden" section in SKILL.md).
4. Change the PR's target branch to `main`: `gh pr edit <N> --base main`. Without it the PR merges into the outdated `feat-a`.
5. Wait for CI on the new commit, then merge (squash, the title explicitly). Repeat from step 1 for the next PR.

**Conflicts during `rebase --onto`:** stop and show the human the files with conflicts. Do not resolve them
automatically. After resolving: `git add <pliki>` and `git rebase --continue`; giving up: `git rebase --abort`.

**Why not cherry-pick:** moving the base keeps the PR in the platform (the "merged into main" marking,
reviews, the discussion), and the history of `main` stays linear, without duplicated commits.

## Sources
- callstackincubator/agent-skills, the `github` skill with the file stacked-pr-workflow.md (the version before the commit
  3bd44da of 2026-08-07, in which the authors removed the skill as outdated), MIT licence; read 2026-10-21.
  Described in our own words; the merge strategy table is our addition.
- `git help rebase` (the `--onto` option); `gh pr merge --help`, `gh pr edit --help`, `gh pr checks --help` in gh 2.89.0
  (checked 2026-10-21): the commit title on a squash is set with `--subject` (`-t`); the `--title` option given in the source
  does not exist in this version.
