# Parallel changes in git worktrees

## 1. Are the changes independent?
| Check | Evidence | Conflict → |
|---|---|---|
| shared files | `git diff --stat` of both plans' file lists | sequential, or split the shared file first |
| contracts | API routes, types, DB schema, events either change touches | agree the contract first, then parallel |
| migrations | both add migrations to the same DB | sequential (ordering and numbering collide) |
| external services | same sandbox account, queue, webhook URL | separate sandboxes or sequential |
Two at a time is the starting point. Raise it only when reviews keep up.

## 2. Setting up
```
git worktree add ../shop-auth   -b refactor/auth-session
git worktree add ../shop-billing -b feat/billing-invoices
```
Per worktree, before starting the agent:
- install dependencies (`npm ci`, `uv sync`, …) — the new directory has no `node_modules` or virtualenv;
- create `.env` from `.env.example` with its own port (`PORT=3001`, `3002`), database name or schema, cache prefix,
  queue or payment sandbox;
- start a fresh agent session inside that directory.
The main checkout stays for coordination: pulling, reviewing, merging.

What a worktree does **not** isolate: ports, databases and their migration state, background services, global caches,
the shared `.git` directory (concurrent fetch/gc can hit `.git/index.lock` — retry after the other command finishes,
never delete the lock while git runs). A branch can be checked out in only one worktree at a time. Each worktree costs disk
for its dependencies.

Cleanup after merging: `git worktree remove ../shop-auth`, then `git branch -d refactor/auth-session`;
`git worktree list` and `git worktree prune` find leftovers.

## 3. Talking between sessions
When one change alters something the other depends on, send at once:
```
Contract change: GET /sessions now returns expiresAt (ISO 8601) instead of ttl, commit 7c2e9b1 in refactor/auth-session.
Required: billing reads expiresAt in src/billing/session.ts. Reply "accepted".
```
The receiving session adapts and replies "accepted"; until then the sender does not merge. This is a lightweight
consumer-acknowledged contract change. Channels in Claude Code: `SendMessage` to a session by name, `/peers` to see them,
`@session-name` in a prompt; text only, and inbound messages can be restricted in settings. `claude agents` lists running
sessions and shows those waiting for you under "Needs input". Without these features, the human carries the message.
[unverified: minimum Claude Code versions — check the current changelog]

## 4. Running mode
- Interactive, phase by phase, when decisions will come up along the way.
- `/goal` with a turn limit when the scope is closed and the end is measurable (core-delivery-lifecycle).
- Each change: its own review, its own PR. An improvement spotted on the side becomes a new plan item, not part of this PR.

Sources: `git help worktree` (git-scm.com); Claude Code docs, parallel sessions and git worktrees (code.claude.com).
