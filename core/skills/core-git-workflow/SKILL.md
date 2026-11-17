---
name: core-git-workflow
description: Use for working with git — branches, commits, pull requests (also agent PRs and auto-merge), their review, conflicts.
metadata:
  review: "2027-10-10"
  catalog: "Use for working with git — branches, preparing commits, pull requests, PR review (also by AI: REVIEW.md, claude-code-action, separation of duties, branch protection), a PR written by an agent (labelling, protected paths, auto-merge), conflicts, dangerous operations. Not for the commit message format (core-conventional-commits) or CI pipelines (the CI/CD skill, pack-it)."
  keywords: "worktree, równolegle dwóch agentów, zmiana kontraktu między sesjami, powiadom drugą sesję, commit fazy, przegląd AI w CI, werdykt przeglądu, skip ci, pull request, PR, code review, przegląd kodu, review przez AI, Claude przegląda PR, REVIEW.md, claude-code-action, ai-review.yml, ai_review.py, workflow przeglądu AI, ochrona gałęzi, branch protection, konflikt, rebase, merge, stos PR, stacked PR, rebase --onto, squash merge, strategia scalania, gh pr merge, zmiana bazy PR, CODEOWNERS, ochrona gałęzi, chronione testy akceptacyjne, agent zmienia scenariusze Gherkin, agent naprawia testy zmieniając je, wymagany check w CI, PR agenta, agent sam otwiera PR, auto-merge, automatyczne scalanie, ścieżki chronione, oznaczenie PR agenta, etykieta PR agenta, two agents in parallel, contract change between sessions, phase commit, AI review in CI, review verdict, Claude reviews the PR, merge strategy, protected acceptance tests, agent PR, agent opens a PR, protected paths, label agent PRs"
---

# Git workflow

## Branches
- Name: `<typ>/<krótki-opis>` e.g. `feat/user-avatar`, `fix/login-redirect`, `chore/deps-bump`.
- Work on a slice or a change with a key (`TSK-57`, `CHG-12`): the key in the branch name in lower case
  (`story/tsk-57-ponowienie-platnosci`), and every commit with the footer `Change: TSK-57` (core-conventional-commits).
  The `commit-msg` hook from this skill rejects a commit without the footer on such a branch. The key comes from the change plan or
  from the human.
- Short-lived branches (hours–days) and frequent integration with the main one (trunk-based, see the delivery skill, pack-it: eng-continuous-delivery).
- You never work directly on `main`/`master`. If you are on it — create a branch before the first change.

## Commits
- The commit message and PR title format: the **core-conventional-commits** skill (also there: how to fix a wrong commit type —
  `--amend` only for the last, unpushed commit and at an explicit request).
- One commit = one logical change; small, frequent commits (easy review and revert).
- A commit fixing something after a PR review or after a task came back for a fix: the trailer `Rework-Cause:` with one value —
  `luka-specyfikacji`, `blad-agenta` (the requirement was clear), `zmiana-wymagan` or `nieznana` (not by default);
  `tf metrics` counts the causes of fixes from them.

## Before a commit
1. `git status` and `git diff --staged` — check that you commit only the intended files.
2. No secrets, `.env` files, dumps, build artifacts.
3. Tests and lint pass.
4. Add files by name (`git add ścieżka`), not `git add -A`, unless the diff is fully reviewed.

## A phase commit (work per a step plan)
- To the index you add **the files touched in this phase** (every Edit/Write) and the step report — not the list from `git status`.
- Show other changed files and ask: only the phase's files (recommended) / everything / abort. You do not include them silently.
- Before the first commit of a new change check whether someone else's previously added files are waiting in the index.
- `git diff --cached --quiet` ends with exit code 0 → there is nothing to commit; you do not create an empty commit.
- Subject: `<typ>(<identyfikator-zmiany>): <tytuł fazy> (f<N>)`; the touched files in the body. `Refs:` only from references
  visible in the conversation or given by the human, never inferred from the branch name.
- The pre-commit hook rejected the commit → remove the cause and make a **new** commit. No `--no-verify` and no `--amend`
  (the commit did not happen, so `--amend` would change the previous phase).
- After the commit add the SHA in the "Progress" section of the step report (core-project-record); at the last phase the SHA and the
  report status go in a separate closing commit.

## Parallel work (several changes at once)
- Start with **two** changes, not five: parallelism is limited by the throughput of human review, not by the number of agents.
- Before starting check independence (an agent can do it from the plans): shared files, contracts (API, types, schema),
  migrations, external services. A conflict → one after another.
- One change = one worktree + one branch + one fresh agent session:
  `git worktree add ../<repo>-<zmiana> -b feat/<zmiana>`; the main directory is for coordination.
  A fork, a new session or a subagent (cost, isolation): `.claude/skills/core-cost-control/references/parallelism.md`.
- **A contract change along the way** (API, types, schema) → a message to the other session right away:
  `Contract change: <what> · <file/commit> · what you have to do · reply "accepted"`. Without "accepted" the other session
  does not merge. The channel: from v2.1.224 `SendMessage` (the session list: `/peers`), from v2.1.232 `@nazwa-sesji`; text only,
  receiving is controlled by `crossSessionInbound`. An older version → the human passes on the same message.
- Which session waits for a decision: `claude agents` (the agents view, research preview) shows a "Needs input" group
  (checked 2026-10-18).
- A worktree isolates files and the branch, **not the environment**: a separate dev server port, a separate local database
  (or schema) and migrations, a separate sandbox of payment and queue services, a separate cache. A fresh worktree has no
  `node_modules` or `.env` — installation and configuration are a start step. Git operations on a shared repository
  can collide on `.git/index.lock`; the same branch cannot be in two worktrees. Tasks touching the same
  ports, databases or files you do not run in parallel; you limit the number of worktrees and clean up forgotten ones
  (`git worktree list`, `git worktree prune`) — the disk cost grows with dependencies.
- A change with decisions along the way → interactively, phase by phase; a change with a closed scope and a measurable end →
  `/goal` with a turn limit (core-delivery-lifecycle). Each change → a review → a separate PR.
- Small improvements discovered along the way you add to the plan as a separate item instead of widening the current change.
- After merging: `git worktree remove ../<repo>-<zmiana>`.

## Forbidden without the human's explicit consent
- `git push --force` (`--force-with-lease` on your own branch is allowed after consent),
- `git reset --hard`, `git clean -fd`, rewriting the history of published branches,
- a push to `main`.

## Pull request
The title like a commit. The description: **What** (1–3 points), **Why**, **How it was tested**, **Risks/rollback**.
A small PR (one change, a few hundred lines) is reviewed faster and more thoroughly than a big one; split a big one into successive PRs.
Refer to the step plan and the requirements (`docs/project/`), so the reviewer checks agreement with the intent.

**Protected acceptance tests are enforced by CI, not by a prompt.** CODEOWNERS only points to reviewers; the enforcement comes from
branch protection ("Require review from Code Owners") and a required check. A change of scenarios goes in a separate PR from the code —
a check in CI rejects a PR that changes both. The number of protected tests does not drop (a supporting alarm: an assertion can be
weakened without changing the number). Changes in step definitions (step definitions, adapters) also go through review, because
a scenario can be "turned green" in the adapter.

**A PR written by an agent.** The agent proposes, the pipeline decides:
- **Labelling:** an agent PR has a label (e.g. `agent`), and its commits a trailer (e.g. `Co-Authored-By:` with the agent's name).
  Review, metrics and audit then tell the agent's work apart from a human's.
- **Protected paths** (`infra/`, auth, payments, `.github/workflows/`, `.claude/`) in CODEOWNERS with "Require review
  from Code Owners". Auto-merge only for PRs that do not touch them. Green CI is not evidence when the PR changes
  the workflow that checks it. `tf risk` marks these paths as high risk.
- **Scope** limited to the task; you revert changes outside it (the `scope-reviewer` agent).
- **Acceptance tests out of the agent's reach** (the point above), so the agent does not "pass" itself.
- **Infrastructure from AI** goes through more gates than a human's, not fewer: a plan of changes in the PR and drift detection.
  A further step: a signed attestation (in-toto, SLSA, Sigstore) with the model, the task and the allowed tools.
- The agent's permissions in CI (secrets, write rights, PRs from a fork): core-agent-security.

## PR review — also by AI
- **The first review can be done by an agent**, the second and deciding one — by a human. The human focuses on behaviour
  ("does it solve the intent?") and risk, not on style, which lint and CI check.
- **`REVIEW.md` in the repository root** describes the review rules (the Code Review service in Claude Code reads it;
  it differs from `CLAUDE.md`, which concerns all of the agent's work). A template: `references/review-md.md`.
- **Tools:** the Code Review service or `anthropics/claude-code-action@v1` in GitHub Actions — it reacts to an `@claude`
  mention in a comment or works automatically with an instruction in `prompt`; configured with `/install-github-app`
  (github.com only), the key in a repository secret (`ANTHROPIC_API_KEY`). The installation and secrets are done by the human.
- **Separation of duties:** the agent does not approve its own code. Protection of the main branch requires the human's approval
  and green CI; the agent can push fixes after comments to the PR branch, but the human merges.
- **Tuning once a month:** assess the accuracy of findings, limit the number of trivia, exclude generated code and what
  CI checks. An untuned review buries the team in comments and stops being read.
- A security review of changes in authentication, IaC and CI: the `security-reviewer` agent before merging.
- **AI review as a CI step** (risk triage, an output contract, the verdict as a commit status, `[skip ci]` for
  bot commits, comments only on diff lines, deduplication): `references/ai-review-in-ci.md`. The blocking gate
  lives in the workflow (a step after the agent reads the verdict), not in the model's answer.
- **A ready workflow:** `python3 .claude/skills/core-git-workflow/scripts/ai_review.py install [--all-prs]` →
  `.github/workflows/ai-review.yml`: a review of PRs with the `ai-review` label (or of every one) per `REVIEW.md`, the agent only
  reads and returns JSON, a workflow step sets the `ai-review/verdict` status and one summary comment, the
  `ai-review-override` label (a human) is a deliberate bypass. Actions pinned to a SHA, `permissions: {}`, a fork block.
  The secret and branch protection are set by the human. `REVIEW.md` from an approved draft of the reconstruction from code:
  `ai_review.py review-md`.
- A review of agreement with the step plan and triage of findings with the human: the change review skill (pack-it: qa-change-review).

## Merging and a PR stack
- One merge strategy in the repository (squash, rebase or merge commit); with squash you give the commit title
  explicitly (the PR title with its number). Choosing the strategy and the commands: `references/merging-and-pr-stacks.md`.
- **A PR stack** (each one targets the previous one's branch): after squashing the first you move the next one with
  `git rebase --onto origin/main <stara-baza> <gałąź>`, push `--force-with-lease` (with consent), change the PR's
  target branch to `main` and merge after green CI. Show conflicts along the way to the human.

## Conflicts
Resolve them understanding both sides — never "take everything mine". After resolving run the tests.

## Sources
- The 10xDevs course, ed. 3 (2026), module 2, lessons 3 and 5 (the phase commit, parallel work) and module 5, lesson 3 (AI review
  in CI) — training material (accessed 2026-10-09); `git help worktree`;
  the Claude Code documentation (code.claude.com/docs: parallel sessions, communication between sessions, `claude agents`),
  accessed 2026-10-18. Described in our own words.
- Merging and a PR stack: callstackincubator/agent-skills, the `github` skill (the version before its removal on 2026-08-07), MIT;
  details in `references/merging-and-pr-stacks.md`.
