# Merging and PR stacks

## 1. Pick one merge strategy per repository
| Strategy | History on main | Choose when |
|---|---|---|
| squash | one commit per PR | small PRs, messy branch history, the PR is the unit of review — a good default |
| rebase | every branch commit replayed, linear | commits are already clean and individually meaningful |
| merge commit | branch commits + a merge node | the fact of merging matters: release branches, long-lived integration branches |
Set it once in the repository settings (allow only the chosen method) and back it with branch protection: required
checks green, required approvals present. Mixing strategies makes `git log`, bisect and revert harder to reason about.

Squash takes its title from wherever the tool picks it unless you set it. Set it:
```
gh pr checks 42            # all required checks green?
gh pr view 42              # approvals, base branch
gh pr merge 42 --squash --subject "fix(auth): refresh token before expiry (#42)"
```
`gh pr merge` has `--subject` and `--body` for the squash/merge commit (see `gh pr merge --help` for your version).
A human merges unless the repository explicitly allows auto-merge for this kind of PR.

## 2. Stacks of PRs
A stack: #1 targets `main`, #2 targets #1's branch, #3 targets #2's branch. Small reviewable pieces, but landing needs care.

**Why it breaks after a squash:** squashing #1 creates a new commit on `main`; #2's branch still contains #1's original
commits. A plain `git rebase main` tries to replay them and conflicts with their own squashed version.

**Landing one level** (repeat for each PR, bottom up):
1. Merge the bottom PR (squash, explicit subject).
2. `git fetch origin main`
3. `git rebase --onto origin/main <old-base-branch> <next-branch>` — replays only the commits after the old base.
4. `git push --force-with-lease origin <next-branch>` — own branch, after the human agreed.
5. `gh pr edit <N> --base main`
6. Wait for CI to go green, get the approval, merge; continue with the next level.

Example: `git rebase --onto origin/main feat/export-query feat/export-endpoint`, then
`gh pr edit 58 --base main`.

Why not cherry-pick onto a new branch: you would lose the PR's discussion, approvals and links; `--onto` keeps the same PR
and a linear history.

## 3. Conflicts during the rebase
- Stop. Show the human the conflicting files and what each side changed. Never resolve automatically and never take one
  side for the whole file.
- After resolving: `git add <files>` and `git rebase --continue`; to back out: `git rebase --abort`.
- Run the tests before pushing.

Sources: `git help rebase` (`--onto`), `git help push` (`--force-with-lease`), git-scm.com; GitHub CLI manual,
`gh pr merge`, `gh pr edit` (cli.github.com); GitHub Docs, "About merge methods on GitHub".
