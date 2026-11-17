# Examples: choosing a model and cost

## 1. Renaming a field across a whole module
**Situation:** "Rename the field `custId` to `customerId` in the orders module — DTOs, mappers and tests". The module has
12 files, the unit tests pass.

**How:**
1. The rubric: tests and types will check the result (yes → a tier lower), git will undo the change (yes → a tier lower), no decision
   (no → a tier lower), no risk (personal data, money, migration — no).
2. 12 files, but per one pattern — no need to split.
3. Start from the cheapest model with a real chance.

**Result:**
```
Delegation: the backend executor, model: haiku
Reason: a mechanical change, checkable with tests and compilation, easy to undo, no decision.
Verification: the module's tests + a type check. Escalation to sonnet only after 2 failed attempts.
```

## 2. Escalation after two failed attempts
**Situation:** An executor on `sonnet` is to fix a test that sometimes passes and sometimes fails (time zone handling
when computing a payment due date). Two fixes — the test still fails every few runs.

**How:**
1. Verification did not pass after 2 attempts → escalation **by one level**, not straight to "everything on max".
2. The rubric confirms: a bug without an obvious cause after an attempt, it concerns money → `opus`.
3. To the new call you add what did not work.
4. After the cause is found, implementing the fix goes back to `sonnet` (de-escalation).

**Result:**
```
Agent(model: "opus")
Task: find the cause of the flaky payment due date test.
What did not work: (1) setting the UTC zone in the test — it still fails; (2) freezing the clock in the test —
it fails at the switch to summer time. Expected: the cause + a plan for the fix, without implementing it.
Then: implementing the plan → Agent(model: "sonnet").
```
The executor on `sonnet` ended its report with the line `Tier: too low — the time bug needed analysis, not execution`; `log_usage` records
it, and for a similar task you choose `opus` for the diagnosis right away.

## 3. A week of work comes out more expensive than assumed
**Situation:** "This week cost more than usual. Check where the tokens are going, and propose a change".

**How:**
1. `python3 .tf/factory/cost_report.py --days 7` — the cost per agent and model, cache hits, `Tier:` signals.
2. You look for a pattern: who often escalates or reports "too high", where cache hits are low.
3. You check the session habits: switching `/model` in the middle of a task, long breaks, `/compact` instead of `/rewind`.
4. You propose a configuration change, not a one-off "be careful".

**Result (a report for the human):**

| Finding | Evidence | Change |
|---|---|---|
| the documentation executor reports "Tier: too high" | report: 4 of 9 tasks | lower the role's tier in `.tf/config/config.yaml` |
| low cache hits in the main session | the status line "cold" after breaks | after a long break a new session from the checkpoint |
| `/model` switched during a task | the session history | the model set at the start; hard steps to an executor with `model: opus` |
| short tasks with the `quality` profile | the advisor called in short tasks | `python3 .tf/factory/profile.py balanced --dry-run`, then the change with consent |
