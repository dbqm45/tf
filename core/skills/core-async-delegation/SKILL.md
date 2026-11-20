---
name: core-async-delegation
description: Use when an agent will work without you watching - cloud sandbox, remote control from a phone, a routine, claude -p or /goal running an approved plan.
metadata:
  review: "2027-11-20"
  catalog: "Use when work is handed to an agent that runs while nobody watches: deciding whether the task qualifies, choosing where it runs and how you get control back (remote control of a local session, cloud sandbox, scheduled routine), writing the contract before launch (scope, setup script, network, secrets, stop condition, budget, review criteria), the no-questions policy for executing an approved plan with claude -p or /goal (bounded repairs, STOP on structural divergence, verdict lines, report), routines that earn permissions step by step, monitoring with a kill switch outside the agent, and the review afterwards. Not for review loops and agent permissions in general (core-agent-security), project phases (core-delivery-lifecycle), session checkpoints (core-project-record) or model choice and cost per task (core-cost-control)."
  keywords: "agent bez nadzoru, zlecić agentowi, sandbox w chmurze, zamknąć laptopa, wrócić rano, praca w nocy, nocny przebieg, plan w nocy, claude -p, /goal, rutyna, codzienna rutyna, zadanie cykliczne, harmonogram agenta, telefon, sterować sesją z telefonu, Remote Control, tmux, SSH, skrypt startowy, setup script, allowlist sieci, sekrety, warunek stopu, limit tur, budżet, max-budget-usd, bez pytań, dwie próby naprawy, STOP, raport, uprawnienia rutyny, drabina uprawnień, komentować zgłoszenia, szkic PR, eskalacja, ten sam bloker, pętla samodoskonalenia, agent poprawia swoje prompty, zestaw ewaluacji tylko do odczytu, inwentarz przebiegów, właściciel przebiegu, wyłącznik awaryjny, kill switch, log poza agentem, unattended agent, cloud sandbox, overnight run, routine, scheduled task, remote control, stop condition, turn limit, budget cap, permission ladder, kill switch, run inventory, self-improvement loop"
---

# Delegating work to an agent nobody watches

Control is moved, not removed: you decide before the start, look in selectively while it runs, and judge the result
afterwards. A green run only proves the infrastructure survived; whether the task is done is decided against criteria
written before the start. The less you watch live, the harder the environment must enforce scope: file and network
isolation are the precondition of autonomy, not an extra.

## 1. Does the task qualify
All of these must hold:
- The done condition is checkable by a command or a checklist, not by taste.
- The file scope can be named: what may be edited, what is read-only, what is off limits.
- No live product decisions and no production access.
- Secrets reduce to none, or to short-lived read-only tokens.
- The outcome is reversible: a branch or draft PR, never a merge or a deploy.

Good fits: updating a test plan, tidying documentation, a small build fix, one backlog slice with an approved plan, issue
triage. Bad fits: fixing a production outage, deciding business rules. For a bad fit, offer the reduced task that does
qualify (e.g. "collect logs and draft a diagnosis on a branch", not "fix production").

## 2. Control mode and budget
The question is: where does the agent run, and when do you get control back?

| Mode | Runs on | You control | Fits | Main risk |
|---|---|---|---|---|
| Remote control of a local session (Claude Code Remote Control, SSH + tmux) | Your machine or VPS | Everything you already have there | Short fix, diagnosis, finishing a task away from the desk | The agent sees your home directory, keys and network; a relay is one more trusted party |
| Cloud sandbox (Claude Code on the web, a managed container) | A fresh container | Setup script, network level, MCP config, secrets, repository scope | A bounded task ending in a PR while the laptop is closed | A badly prepared environment, broad permissions |
| Routine (scheduled or event-triggered run) | Cloud or CI | Trigger, stop condition, budget, success and failure criteria | Recurring triage, reports, checks | Green runs without value, cost, duplicates, loops |

- Only the interface is the problem (you are on the phone, on another network) -> keep the local session and use remote
  control. The agent must be cut off from your home directory, keys and network -> sandbox or a separate VPS.
- Budget is part of the mode: a turn limit, `--max-budget-usd <amount>` (works only with `--print`, i.e. `claude -p`) and a
  wall-clock limit. An agent that proactively messages people also needs a list of data allowed in messages and actions it
  must never take, even when asked.
- Product features, plans and limits change quickly: check the vendor docs before a team rollout.

## 3. Contract before the start
Every line is a decision that would otherwise be made by the agent. Template and readiness checklist:
`references/delegation-contract.md`.
- **Goal and done check** (a command or checklist).
- **Scope**: edit / read-only / forbidden (production code, merge, push to main).
- **Setup by a startup script**, not during the run; keep it short and repeatable - changing the setup script, network or
  secrets usually rebuilds the environment cache.
- **Network allowlist**; often closed after setup, so installing packages mid-run fails by design.
- **MCP and configuration**: only what the environment sees (repository `.mcp.json`); your local user profile is not there.
- **Secrets**: no production ones, none with write rights, minimal scope and lifetime.
- **Stop and budget**: turn limit, `--max-budget-usd`, time.
- **Review criteria up front**: diff only within scope, report lists assumptions and uncertainties, no request for broader
  permissions.
- **Ambiguity rule**: choose the conservative option and report it; do not ask.

Placement rule: what the agent must not be able to do is enforced by configuration (startup script, network policy,
secret store, `--allowedTools`, `--permission-mode`, budget flags). The instruction only says what it should not try.

## 4. Executing an approved plan without a human
Applies to `claude -p "<prompt>" --allowedTools "<list>" --permission-mode acceptEdits --max-budget-usd <amount>` or `/goal`
running `docs/project/<step>/plan.md`. The first unticked item of the plan's progress section is the resume point. No plan
file with runnable verification commands -> do not start; ask for one instead of improvising gates. Full policy with all
line formats (a factory convention): `references/execution-policy.md`.
- **No questions.** Conservative = fewer files, smaller behaviour change, closest to the plan's letter; record it in the
  report. "Not possible within scope" is a valid outcome: STOP and report, never work around the boundary.
- **Before each phase** every verification command in the plan must run; if one cannot, STOP for that phase.
- **Divergence**: minor (a moved file, a new name) -> adapt and log `ADAPT: <what>`; structural (missing dependency,
  different architecture, a previous phase's result absent) -> STOP. In doubt, it is structural.
- **Gates, cheapest first**: the plan's own commands -> stage the phase's files by name -> deliberate breakage of the
  protected behaviour for new or changed tests -> full tests, lint, types -> commit. After each gate print
  `GATE <name>: PASS` or `GATE <name>: FAIL (<short>, attempt k/2)`.
- **Deliberate breakage** (a mutation check): with the files staged, break the behaviour in the working tree, run only that
  test, expect it to fail, then always restore with `git checkout -- <file>`. A test that stays green on broken code protects
  nothing: strengthen the assertion. Never commit the breakage.
- **At most 2 repair attempts per gate**; the third failure is STOP. Never weaken a test, an assertion or a lint rule.
- **Commit only on green**, Conventional Commits (core-conventional-commits), `git add <files>` by name; unrelated dirty
  files are listed as `DIRTY (not added): <files>`; no `--no-verify`, no `--amend`; a failing pre-commit hook is a gate
  failure. Print `COMMIT phase N: <sha>`. Issue ids only if they appear in the plan or conversation.
- **Progress condition for `/goal`** instead of "until it is good": the target is a number from a tool (score, count of green
  tests, p95 latency). Each turn must improve at least one measured value; two turns without improvement -> STOP; the same
  command a third time with an unchanged result -> STOP; plus a turn limit.
- **The end of a turn is a report, not completion.** Long-running models may end a turn with text announcing the next step.
  Keep the task's parts as a checkbox list; open items with no blocker get a short "continue or name the blocker" nudge; the
  done check is made by someone other than the executor (`/goal`'s evaluator, a CI gate). A running background process or
  subagent means the task is still in progress.
- **STOP** (`STOP — <STRUCTURAL DIVERGENCE | GATE FAILURE> in phase <N>`) leaves ticked items ticked, leaves work in progress
  uncommitted, restores any breakage and changes nothing more. A final `REPORT — <step>` is always written, also after STOP.
  Manual verification items are never ticked by the agent; they go to the report's list for the human.

## 5. Routines and recurring runs
- The contract is stricter: goal, stop condition, scope (repository, labels, directories), cost cap (iterations, time,
  budget), **success and failure criteria**. A green technical status can still be a failure: no new items, the same
  conclusion as yesterday, an issue left without a recommendation.
- **Idempotent**: read what the previous run did; today's report exists -> update it, do not add a near-duplicate.
- Trigger on meaningful events or a sensible rhythm, not "every 5 minutes just in case". Self-iterating review loops are not
  scheduled (core-agent-security).
- **Permissions grow with evidence** (least privilege, staged): read-only -> draft in a file -> changes on a branch or
  worktree -> draft of the external action (draft PR, draft comment) -> the action after human approval -> automatic only for
  low-risk actions with a log and a rollback. Move one step only after a series of runs without scope overrun; each new step
  gets its own verification rule. Review routine permissions whenever a tool is added, and monthly.
- Quiet when nothing changed (a one-line status), a full report when a human is needed. The same blocker in two consecutive
  runs -> escalate to a human, not another retry. Judge accuracy by counting correct items, false alarms and misses.
- **Self-improvement loop** (an agent editing its own prompts, skills or hooks): no write access to the permission policy,
  the sandbox, its identity or the evaluation set (keep that set read-only, ideally in a separate repository). A change is
  accepted on a held-out result plus a human's approval, never by the loop itself.
- In-session `/loop` and session-scoped scheduled tasks expire after 7 days; long-lived work goes to a cloud routine.
- Typical failures are mundane: hours of retries against a blocked host, near-duplicate reports, symptom patches,
  branches that cannot be merged.

## 6. Monitoring and stopping
- The phone is a control panel, not a diff viewer. Check: did setup pass, is the run blocked by network, MCP or a secret,
  is scope creeping. Decide: continue, clarify, stop, or leave for review.
- **Inventory of runs**: for each routine and overnight run - owner, permission scope, how to stop it. Review it together
  with permissions.
- **Independent record**: tool-call and network logs collected outside the agent process. The transcript is the agent's own
  account, not evidence.
- **Kill switch outside the agent**: cancel the run, revoke the token, stop the container through the platform. Asking the
  agent to stop is not a kill switch.

## 7. Review afterwards
At a computer: diff, logs, tests and the report against the contract's criteria, not the green status. Within scope and
with evidenced gates -> a review in a fresh context; a human decides the merge. Add one sentence to the project record on
what must change before this mode is safe for the team (core-project-record).

## Example
"Agent in a cloud sandbox completes the payments test plan overnight."

```
Goal: docs/testing/payments-plan.md covers refunds and partial captures; done = checklist in the plan all ticked
Scope: edit docs/testing/**; read src/payments/**; forbidden: src/**, merge, push to main
Setup: startup script installs deps (npm ci); network closed after setup
Secrets: none
Stop: 40 turns or $5 (claude -p ... --max-budget-usd 5), whichever first
Output: branch test-plan/payments + draft PR; report lists assumptions and open questions
Review: diff only in docs/testing/**, every new case traces to a code path (file:line)
```
Morning: the report says `GATE checklist: PASS`, two assumptions about partial-capture limits. You review the draft PR in a
fresh session and decide the merge.

## Sources
- Claude Code docs, "Claude Code on the web" and "Cloud environments", code.claude.com/docs/en/claude-code-on-the-web - accessed 2026-11-20 (setup scripts, network levels, environment cache).
- Claude Code docs, "Remote Control", code.claude.com/docs/en/remote-control - accessed 2026-11-20.
- Claude Code docs, "Scheduled tasks", code.claude.com/docs/en/scheduled-tasks - accessed 2026-11-20 ("Seven-day expiry").
- Claude Code docs, "Run Claude Code programmatically", code.claude.com/docs/en/headless, and `claude --help` of Claude Code 2.1.329 - accessed 2026-11-20 (`--max-budget-usd` only with `--print`, `--permission-mode` values, `--allowedTools`).
- Anthropic, "Prompting Claude Opus 5.5", platform.claude.com - accessed 2026-10-20 (turns ending with an announcement in long tasks).
- OWASP GenAI Security Project, "LLM06:2025 Excessive Agency", genai.owasp.org/llmrisk/llm062025-excessive-agency - accessed 2026-11-20 (least privilege, human approval, independent logging).
