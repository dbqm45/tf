# The delegation contract — template, examples, dry run

## 1. A template to fill in
Copy it into the instruction (move some fields into the environment configuration — the table in §2). An empty field = a decision not yet
made, not "the default".
```text
Goal and the "done" condition: <what has to exist / which command has to pass with exit code 0>
Scope – edit:           <paths>
Scope – read only:      <paths>
Do not:                 <merge, push to main, changes in production code, migrations, dependency changes>
Setup:                  <startup script commands; tools you assume are in the image>
Network:                <off after setup | allowlist: host1, host2>
MCP / configuration:    <only .mcp.json from the repo | none>
Secrets:                <none | name, read-only scope, lifetime>
Stop:                   <condition + turn limit + budget + time>
Ambiguity:              choose the conservative option and write it in the report; do not ask
Report:                 <what was done, assumptions, uncertainties, a list for the human to check>
Review criteria:        <the diff only within the scope; tests/gates with a result; no requests for broader permissions>
```

## 2. Where to set what
| Decision | Environment configuration | Instruction for the agent |
|---|---|---|
| setup, tools | the sandbox's startup script | — (the agent does not install along the way) |
| network | the network policy / allowlist | a mention, so the agent does not try to download |
| MCP | a file in the repo (e.g. `.mcp.json`) | which tools it may call |
| secrets | the environment's secret store | a ban on asking for more |
| tool permissions | `--allowedTools`, `--permission-mode`, project settings | — |
| budget | `--max-budget-usd` (in `claude -p`), the platform limit | the stop condition in words |
| goal, scope, report, criteria | — | yes |

The rule: what the agent **cannot** do is enforced by the environment; the instruction says what it **should not** try.
A change of the startup script, the network or secrets usually invalidates the environment's cache — keep the setup short and repeatable.

## 3. Example: sandbox, a test plan
See the "Example" section in `SKILL.md` (the payments module, network off after setup, no secrets, a limit of 20 turns).

## 4. Example: a daily routine
**Situation:** every morning a review of issues with the `ai-candidate` label.
```text
Goal: a file docs/triage/<date>.md with a list of ai-candidate issues: for each – whether it has reproduction steps,
the likely module, risk (low/medium/high), a recommendation (to an agent / to a human / close).
Scope: read-only access to the issues and the repo; writing only to docs/triage/. No comments on the issues.
Idempotency: if a file with today's date exists, update it; do not create a second one.
Stop: after saving the file or after 15 turns; the budget per run set in the routine's configuration.
Failure despite a green status: no new items despite new issues; recommendations copied from yesterday;
an issue without a recommendation.
```
A weekly review: how many "to an agent" recommendations turned out right; the cost per run; whether the routine still
makes sense.

## 5. Example: remote control of a local session
**Situation:** in the middle of a diagnosis you have to leave; the agent is to finish collecting logs and hypotheses.
- Mode: remote control (Remote Control or SSH + `tmux`) — execution stays on your machine.
- Risk: the agent has access to your home directory and network → no permission-bypass mode, the scope
  limited in words to the diagnosis (no fixes), the session stopped if you do not come back within the agreed time.
- From the phone only decisions: continue / clarify / stop.

## 6. A dry run when the feature is unavailable
An account plan, a company policy or a tool version blocks running it? Write out the contract as if the task were to
go to the team tomorrow, and mark each step:
```text
[done]                          contract filled in, startup script tested locally in a container
[blocked by access]             the cloud sandbox is unavailable on the team's plan – needs an administrator's decision
[to check before rollout]       whether the network allowlist covers the company's package registry
```
The result of a dry run is a list of decisions for the human, not an essay.
