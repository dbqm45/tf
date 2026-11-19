# Buy, extend or build — qualifying an internal tool

AI lowers the cost of a first version, but not the cost of maintenance: responsibility for the data, changes in vendors' APIs,
explaining to the team "why the report is silent today". The question is not "can we build it", but "do we want to
take on this responsibility". A full SaaS replacement also takes on permissions, audit, reliability, onboarding of new
people and data risk.

## Four directions
- **Buy or use a built-in feature** — a generic problem (a ticket summary, labels, a backlog view,
  a CI panel).
- **Extend** (usually the best start) — the value comes from connecting several systems that no SaaS sees
  on its own. A thin layer reads, summarizes, **links to the sources** and does not pretend to be a new source of truth.
- **Build a fuller flow** — only when the extension has survived contact with reality: someone uses it,
  it saves time, it has an owner and a scope.
- **Wait or do not build** — the signal is weak, the problem is solved elsewhere, or the friction is **essential** (it results
  from a real constraint or decision) rather than accidental.

## The opportunity map
One row per friction signal — repeatable and observable ("on Monday a manager spends 40 minutes collecting statuses from three
tools"), not a solution ("let's make a dashboard").
| Friction signal | What existing tools give | A thin extension | The first useful version | Data risk | Direction, if it proves itself |
|---|---|---|---|---|---|
Data risk: mockups, local data, read-only, non-sensitive data → you can go light; real company or customer data
→ access, permissions and audit **before** implementation (arch-privacy-compliance).

## Choosing a candidate (at most one)
A candidate: recurs regularly · connects at least 2 sources or 2 roles · has a manual cost today · can be checked
on an export or in read-only mode · does not take over the responsibility of a platform · has a clear direction of growth.
No signal passes → a "do not build" recommendation with a named existing tool to try.
Better 2–3 maintained tools than 10 prototypes — the limit is the attention needed for maintenance, not the time to start.

## A description of the first version (5–8 sentences)
Reads: [sources] · Returns: [a report, a view, a summary] · Does not do: [deliberate exclusions] · Data risk: […] ·
Direction: [product / feature / internal tool / service / wait].
The order of maturing: a Markdown mockup of the report → a script on JSON or CSV exports → static HTML shared
by hand → only then an agent, a schedule, an application.

## Signals that a tool has become a product
The team plans its day around its output; a wrong report causes confusion; requests appear for new sources,
access control and running without a manual start → a conscious change of status: an owner, error handling,
behavior when data is missing, who sees the result.

## Next step
The cheapest: a few-minute conversation with the manager and the team (they often know the reason for the friction). Then validation by questions
about past behavior (ddd-discovery-intake, `user-research.md`), then requirements (proc-requirements-shaping)
or — with a narrow signal and a clear first version — straight to the plan and implementation.

## Example
**Signal:** "Every Monday a manager spends 40 minutes assembling a status from Jira, GitHub and Slack."
**Map:** Jira and GitHub have separate reports, neither links tickets with PRs and threads → extension: a script reads
exports (read-only), builds a "ticket — PR — last thread" list with links → first version: Markdown
from the exports of the last week → data risk: customer names in tickets (internal only) → direction:
an internal tool, if after 4 weeks the manager uses it.
**Rejected:** your own dashboard with a database and login ("build") — it takes on permissions and maintenance with no proof of value.

Source: 10xDevs course, ed. 3 (2026), module 5, lesson 1 (internal tools, the opportunity map) — training material
(accessed 2026-10-09). Described in our own words.
