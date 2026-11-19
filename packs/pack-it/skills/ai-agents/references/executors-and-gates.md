# Many executors, the witness of a step and long runs

Contents: 1. Many executors over shared state · 2. Who is the witness of this step · 3. Long runs over many
context windows · 4. The harness interface from the model's side · 5. The check before handing over the reply ·
6. Does the agent really work

## 1. Many executors over shared state
- **A task lease with expiry and a heartbeat.** An executor that disappeared loses the task, and another one resumes it
  from durable state.
- **Completion and the write check the current owner and the record version.** A late executor will not overwrite
  a newer result. Writing the whole record from an old copy is a lost update — before the write you check the version
  (compare-and-set, be-database), use a transaction, or one coordinator does the merging.
- **Three different operations:** retry (the same operation once more), resumption (from the saved state; first
  you check whether the versions of documents and configuration still match the accepted work) and compensation (a separate business
  operation, which can also fail). None of them is a universal "undo".
- **Completion is a predicate of the system, not a sentence from the model:** requirements met, validation passed, the artifacts exist,
  policies checked. Explicit exits other than success: an exhausted budget, no new evidence, a requirement to
  clarify. A partial result marked as a "draft with caveats", not as approved.
- **A recovery measure:** how much completed work ran again, whether external writes were duplicated, whether
  accepted evidence disappeared.

## 2. Who is the witness of this step
A step whose only check is further text from the same model is accepted on faith. The rule goes
to a place depending on what it concerns:
| A rule about… | Where | Example |
|---|---|---|
| state | a schema or shape checked on write | "an offer has a `discount` field 0–100" |
| a single action | a per-request policy, deny by default, `forbid` wins over `permit` | "a transfer only to an account from the list" |
| a sequence of actions | a temporal rule over the event log | "a discount > 20% only after a manager's approval within 1 h" |

The gate's verdict (execute / deny / escalate) is repeatable for the same saved state. A rule only in the prompt
or a verdict returned only to the agent guarantees nothing. The log records which witness checked the step. The
`tdd_guard` hook in the factory is an example of a temporal rule ("editing code is allowed if since the last test change there was
a red run").
Source: A. Alcaraz, "Grounded Reasoning For Agents…" (2026-10-20).

## 3. Long runs over many context windows
Anthropic Engineering, "Effective harnesses for long-running agents" (2025-11-26) and "Harness design for long-running
application development" (2026-03-24), read 2026-10-29:
- the first session prepares the environment and a task list, each next one makes one increment and leaves handover
  artifacts (progress, test state); compaction alone is not enough — the agent tries to do everything at once
  and announces the end too early;
- a separate evaluator with explicit criteria; the end rule checked by a test or an evaluator, not by the agent's declaration;
- a read-only reviewer (a report, not a fix — otherwise the signal disappears);
- irreversible tools with `dry_run` enabled by default;
- you resolve the path **before** comparing it with the allowlist: a denylist catches only the anticipated writes,
  and `work/../secrets` gets through (core-agent-security);
- a rule from the prompt that must always work moves to a hook.

## 4. The harness interface from the model's side
- An operation (a unit of intent) is realized by a tool, a composite tool (code, deterministically) or
  a skill (instructions). It matures from a skill to a composite tool once the steps settle.
- A skill refers to tools by id, it does not copy their schemas — one source of truth.
- A small set of primitives (e.g. search memory, list capabilities, find and load an operation, execute, run
  code, ask a human); the harness enforces approval, not the model.
- Channels (Slack, Teams, voice) are adapters normalizing an event to one form — the agent does not belong to the channel.
- Choosing the context (memory, tools) is often classification, not generation: a cheaper selector before the large model,
  measured on your own data (ai-evals).

## 5. The check before handing over the reply
The model copies numbers from tool results and sometimes changes them (a policy limit, a risk score, an amount). The harness checks
this in code before the reply goes out:
- **Numbers and identifiers from the tool:** you extract the numbers, amounts and identifiers from the reply and compare them
  with the values returned by the tools in this run. You send a mismatch back to the model as a concrete message
  ("limit in the reply 50,000, the tool returned 30,000"), with a limit on corrections. After the limit the reply goes to
  a human, not to the customer.
- **Repeated identical calls** (the same tool, the same arguments) you skip and return the previous result.
- **Required tools:** when a tool required for this type of task was not used before the reply, the harness
  reminds the model about it or blocks the reply.
- **Check rules also have false alarms:** substring matching (e.g. "ind" inside other words) blocks good
  replies. You test the rules on real model replies, and measure their accuracy in an evaluation
  (ai-evals, `references/measurement-pitfalls.md` §7–8).

## 6. Does the agent really work
A container "Up" and `/health` returning 200 do not prove that the agent responds. An expired token can route messages
into an empty error-handling branch for a long time without an alarm. A synthetic end-to-end probe: ops-observability,
the section "Healthchecki" (healthchecks).

Sources: V. Mysore, "Harness Engineering … Live Examples" (2026-10, demo); J. Hamidun, "Running a Fleet of 33 AI
Agents" (2026) — incident details per the author [unverified].
