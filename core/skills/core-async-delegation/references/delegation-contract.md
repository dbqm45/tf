# Delegation contract - template and readiness check

Fill this in before an unattended run. Each empty line is a decision you leave to the agent. Keep the filled contract next to
the plan (or in the routine's description) so the review afterwards compares the result with it.

## Template
```
Goal:            <one sentence>
Done check:      <command or checklist that decides done>
Scope - edit:    <paths>
Scope - read:    <paths>
Scope - never:   production code paths, merge, push to main, <other>
Where it runs:   local + remote control | cloud sandbox | routine (trigger: <event or schedule>)
Setup:           startup script <name> (what it installs); nothing installed during the run
Network:         allowlist <hosts> | closed after setup
MCP / config:    servers from the repository .mcp.json only: <list or none>
Secrets:         none | <name>, read-only, expires <when>
Stop:            <turn limit> turns, $<amount> (--max-budget-usd, needs --print), <time>
Output:          branch <name> + draft PR | report file <path>
Ambiguity:       choose the conservative option, record it in the report, do not ask
Review criteria: diff only in scope; report lists assumptions and uncertainties; no request for wider permissions
Owner / stop:    <person>; stop via <platform action: cancel run, revoke token, stop container>
```

For a routine add:
```
Success:         <what a useful run produces>
Failure even if green: no new items | same conclusion as last run | item without recommendation
Idempotency:     <how the run finds the previous output and updates it>
Escalation:      same blocker in two consecutive runs -> <person/channel>
Permission step: <current step on the ladder> ; evidence needed for the next step: <n clean runs>
```

## Where each line is enforced
| Line | Enforced by | The instruction only says |
|---|---|---|
| Scope - never | `--allowedTools`, `--permission-mode`, branch protection | "do not try to merge or push to main" |
| Network | Environment network level / allowlist | "do not install packages during the run" |
| Secrets | Secret store; token scope and expiry | "do not ask for other credentials" |
| Stop | `--max-budget-usd`, turn limit, platform timeout | "stop and report when the limit is near" |
| Owner / stop | Platform controls outside the agent | nothing - the agent cannot be its own kill switch |

## Readiness check when the feature is not available yet
When the feature, plan or version you need is not available to you yet, fill the template anyway and add a column per
line: what is missing (nothing / an access or licence / an unknown fact) and who resolves it. The output is a list of
requests and open questions for the human, not a run.

## Example (routine)
```
Goal: weekly triage of issues labelled ai-candidate into a report
Done check: report docs/triage/<date>.md exists, every issue has a recommendation or "needs human"
Scope - edit: docs/triage/** ; read: issues via read-only token ; never: comments, labels, closing issues
Stop: 30 turns, $3
Failure even if green: zero new issues for 3 runs (check the label filter), same recommendations as last week
Escalation: the same API error twice in a row -> the routine owner
Permission step: read-only + file draft; next step (draft comments) after 4 clean runs
```
