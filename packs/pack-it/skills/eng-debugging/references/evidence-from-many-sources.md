# Investigation from many sources of evidence

No single source is enough. In the report, list what each channel contributed.

## A report from a user
One sentence without a stack trace ("saving a note does not work") you break down into questions, not into a diagnosis: reproduction steps,
scope (what works, what does not), frequency, since when, the suspected area.

## Where to start
| Symptom | First source |
|---|---|
| an exception, 5xx, a crash | error monitoring (stack trace, the trail of events before the error, the request context) |
| "success", but the effect does not happen (200, data unchanged) | monitoring + application logs (warn/error without propagation) |
| a problem only in the UI, the API healthy | the browser: console, network traffic, accessibility tree |
| a failing test | the test result and stack trace, then the code |
| random or only in production | monitoring (frequency, versions, users), logs with a request identifier |

## Channels and what they give
- **Error monitoring** (Sentry or an equivalent, also through MCP): the place and name of the error, the stack, the events before the error.
  A console warning gets there only with console capture turned on — that uses up the event quota; with traffic
  narrow it down to errors or report selected cases explicitly.
- **Application/platform logs** (with a filter on the message): the scale — a single incident or every call.
- **The browser** (Playwright: the console, the list of requests, the details of one request): separates the front end from the backend.
- **Code**: the root cause — read only with a hypothesis from the previous channels.

## A visual signal (only pixel bugs)
Overlapping, z-index, truncated text, an animation — the console and the network are silent. A screenshot and an open question to a model
with the image; the answer is a hypothesis (models confuse positions and can report a false alarm or miss a problem).
Visual regression in tests you check with deterministic tools (qa-regression), not with a model.

## The reproducing test
It fails for the right reason and checks **the durable effect** (a row in the database, a file, a sent message), not the response status.
It stays as a regression guard.

## A swallowed error — a fix in two parts
1. **Stop hiding:** return an error (5xx or a domain code), not a "success" with data from memory.
2. **Fix the operation itself.** Part 1 alone turns a silent 200 into a visible 500 — only both together make it work.

Search the code for the same pattern (error handling that logs and returns success) — there are usually several copies
(eng-clean-code, the "Errors" section).

## Verification = the mirror of the investigation
Every channel that showed the problem must show its absence: a green test, no new events in monitoring, no
message in the logs, a correct flow in the browser.

## Why the gates did not catch it
Add an escape analysis (qa-test-design, `test-strategy-and-plan.md`): a risk named in the test strategy, but without
a built test phase, is not yet a gate.

## A hook showed a failing test
The agent fixes trivial things (format, import, type) itself. A business logic test still fails after 1–2 fix attempts → stop and this
procedure (or a separate change); you do not fix the code "by intuition" until it is green (eng-local-quality-gates).

## Sources
- The 10xDevs course, ed. 3 (2026), module 3, lesson 5 (debugging with monitoring, logs and the browser) — training
  material (accessed 2026-10-09).
Described in our own words.
