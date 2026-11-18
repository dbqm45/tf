# Agent failures and remedies

## Failures
| Symptom | Cause | Remedy |
|---|---|---|
| looping, the same calls | no limit, an unclear goal, the tool does not return progress | a step limit, detection of repetitions, an explicit end state |
| wrong tool choice | too many, overlapping descriptions | consolidation, namespaces, boundaries in the description |
| wrong arguments | ambiguous parameters | an enum, unambiguous names, poka-yoke, an error with the fix |
| a double action after a timeout | a write without idempotency | an idempotency key, a state check before the write |
| a goal lost after long work | an overfull context | compaction, a progress file, a subagent with a clean context |
| an error in step 3 breaks step 9 | accumulating state errors | code gates between steps, checkpoints, resumption |
| the cost grows without a better result | multi-agent or an agent where a workflow is enough | go back to a lower rung, measure the cost per case |
| a command from the content executed | data treated as instructions | data ≠ commands, no outbound channel next to confidential data |
| subagents duplicate work | an underspecified task | goal, format, boundaries and tools in the assignment |
| "works on the demo" | no set of cases | 10–20 cases, then extending from production |

## The human approval pattern
The agent prepares the action (`refund_prepare` → a draft with the amount, the recipient, the effect), a human approves in a separate
channel, and only the code executes `refund_execute` with an idempotency key. The model has no tool that executes without this step.

## What to log in the trace
The run id, the step number, the call (name, arguments, shortened result), input and output tokens, time, the decision
to end, the prompt and model version. Mask or omit personal data in traces.

## An agent operating a program
Before the agent gets screenshots, you look for a higher interface, in this order: the program's own file format →
the command line (headless mode) → scripts or automation (e.g. COM) → the official API → the accessibility tree (control
names as text) → pixels last. Every rung higher is faster, cheaper and resistant to changes in appearance.
- **Every function as a tool with a contract:** an argument schema, an implementation, a **verifier** (reading the result
  back, e.g. reopening the saved file with another reader) and an **effect** — `local` or `outward`. An action
  going out to other people (sending, publishing) waits for a human's consent.
- The tool result is a short JSON with a list of the checks performed. A tool refusal gives the reason and a feasible alternative.
- The tool list narrowed to the groups matching the request, not all schemas in every call. A chain of dependent
  calls you plan in one model call, with references to the results of earlier steps.
- A successful run can be compiled into a new tool with parameters. You replay it only when the window matches
  the learned one, and disable it after 2 failures.
- The risk classifier for UI actions runs in code, not in the model, because the text on the screen can carry command injection.
- Checks prove numbers, not sense: a bad plan can pass all the verifiers. A human looks at a result going
  outside.

Source: F. Khan, "Building Fast Computer Agents to Solve Complex Tasks" (2026-10-07); the author's numbers from a single
setup [unverified].
