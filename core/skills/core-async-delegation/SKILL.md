---
name: core-async-delegation
description: Use when an agent is to work unsupervised (claude -p, /goal, sandbox, routine) — a contract, gates, review.
metadata:
  review: "2027-10-09"
  catalog: "Use when you hand a task to an agent that works without a human at the screen — remote control of a local session from a phone, a cloud sandbox (laptop closed), a routine or scheduled run, executing an approved plan with claude -p or /goal — qualifying the task, choosing the control mode, a contract before the start (goal, scope, setup, network, MCP, secrets, stop, budget), a policy for executing a plan without questions (gates in phases, deliberate breakage, at most 2 repair attempts, a STOP block, commit on green, a report), monitoring and the review afterwards. Not for the review loop and agent permissions (core-agent-security), project phases (core-delivery-lifecycle), a session checkpoint (core-project-record) or choosing a model (core-cost-control)."
  keywords: "bez nadzoru, w tle, w nocy, zamknięty laptop, odejść od komputera, z telefonu, remote control, sandbox w chmurze, claude code on the web, codex cloud, rutyna, harmonogram, routine, claude -p, headless, /goal, delegacja, zlecić agentowi, agent sam wykona plan, praca asynchroniczna, nocny agent, agent poprawia własne prompty i skille, pętla samodoskonalenia, agent sam commituje zmiany, granice dla agenta, uprawnienia rutyny, unsupervised, in the background, overnight, closed laptop, from my phone, cloud sandbox, schedule, delegate to an agent, agent executes the plan alone, asynchronous work, overnight agent, self-improvement loop, routine permissions, kontrakt przed startem, warunek gotowe, warunek stopu, limit tur, budżet przebiegu, najwyżej 2 próby naprawy, nie osłabiaj testu, blok STOP, raport końcowy, koniec tury to raport, zapowiedź kolejnego kroku, warunek postępu, aż będzie dobrze, dwie tury bez poprawy, przebieg cykliczny, codzienna rutyna, przegląd zgłoszeń, uprawnienia rosną z dowodem, zielony przebieg bez wartości, ta sama próba w kółko, polecenie na noc, wykonanie planu bez pytań, contract before the start, stop condition, turn limit, at most 2 repair attempts, end of turn is a report, progress condition, recurring run, permissions grow with evidence"
---

# Delegating work to an unsupervised agent

Control does not disappear, it moves: **you configure before the start, monitor selectively, assess after
it ends.** A green run means only "the infrastructure did not fall over", not "the task is done". The less you watch
the run live, the tighter the environment has to enforce the scope — isolation of files and network is a precondition
of autonomy, not an obstacle.

## 1. Is this a task to hand over
Yes, when all of these are true:
- the "done" condition is checked by a command or a checklist (tests, a file, a report), not by taste;
- the scope of files can be named (edit / read only / do not touch);
- it does not require live product decisions or access to production;
- secrets can be reduced to zero or to short-lived ones, without write rights;
- the result is reversible: a branch or a draft PR, never a merge or a deployment.

Good: updating a test plan, tidying documentation, a small setup fix, a slice of the backlog with a plan,
reviewing pending issues. Bad: "fix production", "decide how the discount should work".

## 2. The control mode — the question "when does the human get control back?"
| Mode | Where the agent runs | What you control | Fits | Main risk |
|---|---|---|---|---|
| **remote control of a local session** (Remote Control in Claude Code, SSH + `tmux`, a relay like Happy) | your machine or a VPS | the session itself, from another device | a short fix, a diagnosis, finishing work | the machine's security is on your side; a relay = an extra party to trust |
| **cloud sandbox** (Claude Code on the web, Codex Cloud) | a managed container | setup, network, MCP, secrets, scope | a bounded task up to a PR with the laptop closed | a badly prepared environment, permissions too broad |
| **routine / recurring run** (schedule, event, API) | cloud or a server | the trigger, the stop condition, the budget, the success criteria | a report, a review of the backlog, a check after a release | green without value, cost, duplicates, looping |
| **proactive agent** (writes to the user on its own: a digest, a reminder) | cloud or a server | the rhythm and the list of topics (set by the user), data classes in messages, actions forbidden even with consent | a morning digest, a deadline reminder | a leak in a message, noise, the cost of constant checking (check every few hours) |

A problem only with the interface (a phone, another network) → a local agent + remote control. You want to cut the agent off from
your home directory, keys and network → a sandbox or a separate VPS. The features of these products (account plans, versions,
limits, cache) change quickly — before rolling it out in a team check the vendor's documentation.

## 3. The contract before the start
Each line is a decision you will make anyway — better before the start than after the first failure. Part goes into
the environment configuration (setup, network, secrets), the rest into the instruction:
1. **goal and the "done" condition** — checkable;
2. **scope** — files to edit, read-only files, what not to do (production code, merge, push to `main`);
3. **setup** — dependencies installed by the startup script, not "along the way"; tools from the base image listed explicitly;
4. **network** — an allowlist of hosts; often turned off after setup, so "install a package along the way" will not work;
5. **MCP and configuration** — only what the environment sees at start (e.g. `.mcp.json` in the repo); the user's local
   profile is invisible in the cloud;
6. **secrets** — no production ones and none with write rights; minimal scope and lifetime;
7. **stop and budget** — a limit of turns and cost (`claude -p … --max-budget-usd <kwota>`), time;
8. **review criteria** — up front: the diff only within the scope, a report with assumptions and uncertainties, no request
   for broader permissions.

A template to fill in, an example and a "dry run" variant: `references/delegation-contract.md`.

## 4. Executing a plan without a human
When you delegate an approved step plan (core-delivery-lifecycle, core-project-record), the agent gets a policy
instead of questions:
- **No questions to the user.** Ambiguity → the conservative option (fewer files, a smaller change of behaviour,
  closest to the letter of the plan), written in the report.
- **"Not possible within the scope" is a correct result:** STOP and a report, not getting around the boundary (core-agent-security §4).
- **Before the start** it checks that every verification command from the plan can be run; missing = STOP in that phase.
- **Divergence from the plan:** minor (a moved file, a new name) → adapt and write `ADAPT: …`; structural (a missing
  dependency, a different architecture, no result of the previous phase) → STOP. When in doubt — structural.
- **Phase gates, cheapest first:** the commands from the plan → the phase's files added to the index by name → **deliberate breakage**
  for new tests (pack-it: qa-spec-first-testing) → full tests, lint, types → commit. After each gate the line
  `GATE <nazwa>: PASS` or `FAIL (<skrót>, attempt k/2)` — the `/goal` evaluator sees only the transcript.
- **At most 2 repair attempts per gate;** the third failure = STOP. It does not weaken a test, an assertion or a lint rule.
- **A progress condition, not "until it's good".** The `/goal` target is a number from a tool (a Lighthouse score, the number of
  green tests, p95 time). Next to the turn limit: every turn improves at least one measured metric; two turns
  without improvement = STOP. The same command a third time without a change in the result = STOP.
- **Commit only on green** (core-conventional-commits), files by name; dirty files outside the phase it lists,
  does not add; no `--no-verify` or `--amend`; a hook failing before the commit = a gate failure.
- It does not tick off manual verification — a list for the human at the end. The progress state only in the plan (the first
  unticked item = the place to resume).
- At the end a **report**: phases with SHAs, adaptations, uncertainties, the manual verification list, a proposal of a review
  in a fresh context.

The format of the STOP block, the report and a `/goal` command to copy: `references/execution-policy.md`.

**The end of a turn is a report, not completion.** Newer models (Opus 5.5) in a long task sometimes end a turn with text alone
— a summary announcing the next step. A loop that takes this as the end stops the work halfway:
- you keep the parts of the task on a list (a plan with checkboxes, a task list); open items without a named blocker
  → a short message "open: <pozycje>; continue, and if blocked write what blocks you";
- the "done" condition is checked by someone other than the executor (`/goal` with a small evaluator model, a gate in CI);
- a running background process or a subagent = the task continues; you wait for its result;
- in an orchestration of several agents give a time budget ("how much is left") — in Anthropic's tests teams finished faster
  at similar quality (platform.claude.com, "Prompting Claude Opus 5.5", 2026-10-20).

## 5. Routines and recurring runs
- A stronger contract than for a single run: **goal, stop condition, scope** (repo, labels, directories),
  **a cost limit** (iterations, time, budget), **success criteria** and **failure criteria** (when a green technical
  status is still a failure — e.g. a report without new items, the same conclusion as yesterday).
- Idempotency: a run checks what the previous one already did (today's report exists → it updates it, does not duplicate it).
- The trigger is an event that matters, or a sensible rhythm — not "every 5 minutes just in case".
- A loop that iterates on its own until the reviewer accepts does not go into a schedule (core-agent-security §5a).
- **Permissions grow with evidence.** The ladder: read only → a draft in a file → changes on a branch or in a worktree → a draft
  of an external action (a draft PR, a draft comment) → an action after the human's consent → automation only for low-risk
  actions, with a log and a way back. A rung up only after a series of runs without exceeding the scope,
  and each new rung gets a new verification rule. You review a routine's permissions with every new tool
  and every month.
- **Two result modes:** *silence* (a short state update when nothing changed) and *attention* (a report when something
  needs a human). The same blocker in two consecutive runs = escalation to a human, not another retry.
- **An accuracy review** counts accurate items, false alarms and misses, not only what the routine found.
- **A self-improvement loop** (the agent improves its own prompts, skills, hooks): it has no write access to the permission policy,
  the sandbox, the identity or the evaluation set — those live in a separate repo or are read only. A change is accepted by
  the result on a held-out set and by a human, not by the loop itself (pack-it: ai-evals, the harness change gate).
- `/loop` lives in the session and expires after 7 days (code.claude.com/docs/en/scheduled-tasks, "Seven-day expiry", read
  2026-10-29); work that has to outlive the session goes to a cloud routine.
- Typical failures are boring: hours of attempts to fetch from a blocked host, a second similar report, patching a symptom
  instead of the cause, a branch nobody can merge.

## 6. Monitoring
A phone is a control panel, not a place to review a diff. You check: whether the setup passed, whether a network,
MCP or secret block stopped the work, whether the agent is widening the scope. The decision: continue / clarify /
stop / leave for review.
- **An inventory of runs:** every routine and run has an owner (who started it), a permission scope and a way to
  stop it. The inventory review goes together with the permissions review (§5).
- **A record the agent cannot rewrite:** a log of tool calls and network traffic collected outside the agent's process.
  The agent's transcript is its account, not independent evidence.
- **A kill switch without the agent's cooperation:** stopping through the platform (cancelling the run, revoking the token, stopping
  the container), not asking the agent to stop.

## 7. The review afterwards
At the computer: the diff, logs, tests and the report against the contract's criteria — not against the green status. Changes
within the scope and gates with evidence → a review in a fresh context and the human's decision on merging. At the end one sentence
for the project record: what has to change for this mode to be safe for the team (core-project-record).

## Example
**Situation:** "After the change of subscription limits I want the agent in a sandbox to complete the test plan of the payments module,
and I'll close the laptop."

**Result (instruction + configuration):**
```text
/goal Done when docs/test-plans/payments.md has scenarios for the new subscription limits
(min. over the limit, exactly at the limit, a plan change mid-period) and a short gap report.
Scope: edit only docs/test-plans/payments.md; src/modules/payments/** read only. No merge or push to main.
Setup: npm ci in the startup script. Network: off after setup. MCP: only .mcp.json from the repo.
Secrets: none. Stop: after the report or after 20 turns; budget set in the configuration.
Review: the diff covers only the test plan; the report lists assumptions and uncertainties; no request for secrets.
```
Mode: sandbox (laptop closed, a task without secrets). In the morning: a diff in only one file, a report with 2 uncertainties
→ review and a PR. A conclusion for the record: "the sandbox needs read-only access to the limits specification".

More: `references/delegation-contract.md` (template, dry run), `references/execution-policy.md` (STOP, report).

## Checklist
- [ ] the task passes the qualification from §1 (checkable, a named scope, no production and no secrets, reversible)
- [ ] the mode chosen with the question "when do I get control back"
- [ ] the contract: goal, scope, setup, network, MCP, secrets, stop, budget, review criteria
- [ ] with a plan: no questions, the conservative option, gates with verdict lines, ≤2 attempts, STOP, commit on green
- [ ] a routine: failure criteria despite a green status, idempotency, a cost limit
- [ ] the review afterwards against the contract; the conclusion written in the record

## Sources
- The 10xDevs course, ed. 3 (2026), module 5, lesson 5 (asynchronous and remote work) and the course's skill for the autonomous
  execution of a plan from lesson 5 — training material (accessed 2026-10-09).
- `claude --help`, Claude Code 2.1.296 (checked 2026-10-10): `--max-budget-usd` (only with `--print`),
  `--allowedTools`, `--permission-mode` (`acceptEdits`, `auto`, `bypassPermissions`, `manual`, `dontAsk`, `plan`),
  `--remote-control`, `--json-schema`. The `--max-turns` option is not listed in the help [unverified].
- Anthropic: "Claude Code on the web", "Remote Control", "Routines"; OpenAI: "Codex Cloud environments" — according to the course,
  not opened directly [unverified details: account plans, minimum versions, limits, cache].

Described in our own words.
