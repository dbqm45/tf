---
name: core-git-workflow
description: Use when branching, committing, pushing, opening or reviewing a PR, merging, running parallel worktrees or resolving conflicts — safe git for humans and agents.
metadata:
  review: "2027-05-20"
  catalog: "Use when you name a branch, stage and commit, commit a plan phase, push (force-with-lease), run several agents in parallel git worktrees, open a pull request (also one written by an agent), set up AI review of PRs (REVIEW.md, claude-code-action, the ai_review.py workflow with the ai-review/verdict status), choose a merge strategy, land a stack of PRs after a squash (rebase --onto), resolve a conflict or ask whether a destructive git command is allowed. Not for the commit message format (core-conventional-commits) or CI pipelines (ops-ci-cd, pack-it)."
  keywords: "gałąź, nazwa gałęzi, nowa gałąź, praca na main, commit, zrób commit, zacommituj, commit fazy, git add -A, co dodać do commita, push, git push --force, force push, force-with-lease, push odrzucony, rebase, rebase --onto, reset --hard, git clean, przepisanie historii, pull request, otwórz PR, opis PR, przegląd PR, code review, przegląd przez AI, Claude przegląda PR, REVIEW.md, claude-code-action, ai_review.py, werdykt przeglądu, status commita, blokada scalenia, ochrona gałęzi, branch protection, CODEOWNERS, wymagany przegląd, scalanie, squash, merge commit, strategia scalania, stos PR, stacked PR, PR na PR, konflikt, konflikt scalania, rozwiązać konflikt, worktree, git worktree, równolegli agenci, dwie sesje równolegle, zmiana kontraktu, index.lock, port zajęty, PR od agenta, auto-merge, automatyczne scalanie, chronione ścieżki, testy akceptacyjne w CI, klucz zmiany w gałęzi, stopka Change, Rework-Cause, branch name, make a commit, commit my changes, stage files, force push rejected, push rejected after rebase, open a pull request, PR description, review a PR, AI code review, Claude reviews pull requests, required status check, merge strategy, squash or rebase, stacked pull requests, merge conflict, parallel agents, git worktrees, contract change, agent opened PR, auto-merge, protected paths, destructive git command"
---

# Git workflow — branches, commits, PRs, review, merge

The commit message format belongs to core-conventional-commits; this skill covers everything around it.

## Never without the human's explicit consent
`git push --force` (and `--force-with-lease`), `git reset --hard`, `git clean -fd`, rewriting history that was pushed,
pushing to `main`/`master`. Ask first, say what will be lost, offer the safe alternative.
- Diverged own branch after a rebase → `git push --force-with-lease` on *your own* feature branch, after consent. It
  refuses if someone else pushed in the meantime. Never force to `main`/`master` or a shared branch.

## Branches
- Branch before the first edit; never commit directly on `main`/`master`.
- Name: `<type>/<short-description>`, e.g. `fix/login-timeout`. Work with a change key carries it in lower case:
  `story/tsk-57-csv-export`, and every commit on it has the footer `Change: TSK-57` — the commit-msg hook of
  core-conventional-commits rejects a commit on such a branch without it. The key comes from the change plan or the human;
  you never invent one.
- Keep branches short-lived and integrate often (trunk-based; details in eng-continuous-delivery, pack-it).

## Commits
1. `git status`, then review what goes in: `git diff` and after staging `git diff --staged`.
2. Stage by explicit path. `git add -A` / `git add .` only when you have read the whole diff.
3. Nothing that should not be versioned: `.env`, keys and tokens, dumps, build output, large binaries.
4. Tests and lint pass before the commit.
5. One logical change per commit; message per core-conventional-commits. A wrong message: amend only the last
   commit, only if unpushed, only on request.
- A fix after review or rework carries `Rework-Cause:` with `spec-gap`, `agent-error`, `requirement-change` or `unknown`.
  Choose the real cause; `unknown` is not a default. `tf metrics` counts them.

**Commit per plan phase** (factory convention):
- Stage only the files this phase touched plus its step report. Other changed files → show them and ask: this phase only
  (recommended) / everything / stop. Before the first commit of a change check the index for files staged earlier by
  someone else.
- `git diff --cached --quiet` exits 0 → nothing staged; make no empty commit.
- Subject `<type>(<change-id>): <phase title> (f<N>)`, files listed in the body. `Refs:` only with references the human
  gave or that appear in the conversation — never derived from the branch name.
- A hook rejects the commit → fix the cause and commit again. No `--no-verify`, no `--amend` (it would rewrite the
  previous phase's commit).
- After the commit put its SHA in the step report's Progress list (core-project-record); the SHA of the last phase and the
  final report status go in a separate closing commit.

## Parallel work
Start with two changes at a time — the limit is how much the human can review, not how many agents can run.
1. **Independence check:** shared files, API/type/schema contracts, migrations, external services. A conflict → run them
   one after another.
2. **One change = one worktree + branch + fresh session:** `claude --worktree <change>` (`-w`) creates
   `.claude/worktrees/<change>/` on a new branch `worktree-<change>` from the default branch (`worktree.baseRef: "head"`
   branches from your HEAD) and starts the session there; add `.claude/worktrees/` to `.gitignore`. A `.worktreeinclude`
   file at the root (`.gitignore` syntax, e.g. `.env`, `.env.local`) copies those gitignored files into each new worktree;
   tracked files are never copied. On exit a clean worktree is removed, one with work asks; a `-p` run leaves it
   (`git worktree remove`). Fallback when `--worktree` does not fit (a named or existing branch, a directory outside the
   repo, no native worktrees): `git worktree add ../<repo>-<change> -b feat/<change>`, then `git worktree remove`. The main
   checkout only coordinates; strays: `git worktree list`, `git worktree prune`.
3. **A worktree isolates files and the branch, not the environment.** Give each its own dev-server port, local database
   or schema (migrations!), queue/payment sandbox, cache. A fresh worktree has no `node_modules`, and no `.env` unless
   `.worktreeinclude` names it. Git operations on the shared repository can collide on `.git/index.lock`. One branch
   cannot be checked out in two worktrees. Disk use grows with dependencies.
4. **Contract change mid-flight:** message the other session at once, in this shape:
   `Contract change: <what> in <file/commit>. Required: <action>. Reply "accepted".` (PL: „Zmiana kontraktu … odpowiedz
   «przyjęte»”). The other side does not merge until it replied "accepted". Channels: `SendMessage` to a named session,
   `/peers` to list them, `@session-name` in a prompt; without them the human relays. `claude agents` groups sessions that
   wait for you under "Needs input".
5. Choose how each runs: decisions along the way → interactive, phase by phase; closed scope with a measurable end →
   `/goal` with a turn limit (core-delivery-lifecycle). Each change gets its own review and its own PR; side improvements
   become new plan items. Cost of parallel sessions: `.claude/skills/core-cost-control/references/parallelism.md`.
Details and a session checklist: `references/parallel-worktrees.md`.

## Pull requests
- Title like a commit subject. Body: What (1–3 points), Why, How it was tested, Risks and rollback; link the plan or
  requirements in `docs/project/`.
- Small: one change, a few hundred lines. Split anything bigger.
- **Agent-authored PRs — the agent proposes, the pipeline decides:**
  - mark them with a PR label (e.g. `agent`); an unattended routine commits as its own bot identity in git. No AI
    co-author trailer: in a session a person drives, the author is that person's git `user.name`/`user.email` alone;
  - protected paths (`infra/`, auth, payments, `.github/workflows/`, `.claude/`) have owners in CODEOWNERS and are
    excluded from auto-merge; a green run proves nothing when the PR edits the workflow that produced it; `tf risk` rates
    these paths high;
  - scope stays with the task, out-of-scope edits are reverted (`scope-reviewer` agent);
  - AI-written infrastructure gets more gates, not fewer. Agent permissions in CI: core-agent-security.
- **Protected acceptance tests** are enforced by settings, not by the prompt. CODEOWNERS only names reviewers; it binds with
  branch protection "Require review from Code Owners" plus a required check. Scenario changes go in a separate PR from
  code — a CI check rejects a PR that changes both. Guard step definitions and adapters too: a scenario can be turned green
  there.
Details: `references/agent-prs.md`.

## Review, including AI review
- An agent may do the first pass; the deciding review is human and looks at behaviour and risk, not style.
- Separation of duties: an agent never approves its own code. Branch protection requires a human approval and green CI;
  the agent may push fixes to the PR branch; a human merges.
- Rules live in `REVIEW.md` in the repo root (not in CLAUDE.md): template `references/review-md.md`. A draft from code
  reconstruction becomes `REVIEW.md` with `ai_review.py review-md` after the human approves it.
- Tools: the Claude Code Code Review service or `anthropics/claude-code-action@v1` (answers `@claude`, or runs a
  `prompt`), installed with `/install-github-app`. The human installs the app and sets secrets.
- **The factory's ready workflow:**
  1. `python3 .claude/skills/core-git-workflow/scripts/ai_review.py install` (add `--all-prs` to review every PR, not
     only those labelled `ai-review`) writes `.github/workflows/ai-review.yml`; it refuses to overwrite without `--force`.
  2. Add the repository secret `ANTHROPIC_API_KEY`.
  3. In branch protection require the status `ai-review/verdict`.
  4. `REJECTED` or a missing/invalid result → red status; a human can bypass with the label `ai-review-override`.
  Fork PRs are skipped (no secrets for them). How the gate works and what breaks it: `references/ai-review-in-ci.md`.
- Tune monthly: check how many findings were right, cap trivia, exclude generated and CI-covered files. Security-relevant
  changes (auth, IaC, CI) → `security-reviewer` before merge. Review against the plan with the human → qa-change-review (pack-it).

## Merging, stacks, conflicts
- One strategy per repository, enforced in its settings: squash (small PRs, clean history), rebase (linear history keeping
  each commit), merge commit (when the merge record matters, e.g. release branches). With squash set the title yourself:
  `gh pr merge 42 --squash --subject "feat(export): CSV export (#42)"`. Merge only with green CI and required approvals.
- After squashing the base of a stack, the next PR still carries the old commits:
  `git fetch origin main` → `git rebase --onto origin/main <old-base-branch> <branch>` →
  `git push --force-with-lease` (own branch, after consent) → `gh pr edit <N> --base main` → wait for CI → merge.
- Conflicts: understand both sides, never take "ours" wholesale, run the tests afterwards. During a rebase stop and show the
  human the files; continue with `git add` + `git rebase --continue`, or `git rebase --abort`.
Details: `references/merging-and-pr-stacks.md`.

## Example
Request: "Ship the CSV export; push it however." Branch `story/tsk-57-csv-export`, phase 2 of 3 done. `git status` shows
`src/export/csv.py`, `tests/export/test_csv.py`, the step report `012-csv-export.md` and an unrelated
`config/local.yaml`. The agent stages the first three by path, asks about `config/local.yaml` (answer: leave it), checks
`git diff --staged`, commits `feat(TSK-57): endpoint and serializer (f2)` with `Change: TSK-57`. The pre-commit hook fails on
a lint error → fixed, new commit `d4e81a2`, SHA added to Progress. The remote rejects the push because the agent rebased on
`origin/main`: it asks, then runs `git push --force-with-lease origin story/tsk-57-csv-export` — never `--force` and never
to `main`.

## Sources
- Git documentation: `git help worktree`, `git help rebase` (`--onto`), `git help push` (`--force-with-lease`), git-scm.com.
- GitHub Docs: protected branches and required status checks, CODEOWNERS, commit statuses API (docs.github.com).
- GitHub CLI manual: `gh pr merge` (`--subject`), `gh pr edit --base` (cli.github.com).
- Claude Code docs, "Run parallel sessions with worktrees", code.claude.com/docs/en/worktrees - accessed 2026-11-24
  (`--worktree`, `.worktreeinclude`, `worktree.baseRef`, cleanup, manual `git worktree add`).
- Claude Code docs (code.claude.com): GitHub Actions / `anthropics/claude-code-action`, Code Review, parallel sessions.
  The cross-session commands (`SendMessage`, `/peers`, `@session-name`, `claude agents`) are recent [unverified: check the
  version in the current changelog].
