# Internal tools — buy, extend, build or wait

Used by proc-product-discovery (step 0) when someone proposes an internal tool or automation: "a dashboard that pulls
everything together", "an agent that writes the weekly report".

## Why qualify first
A code assistant makes the first version cheap; it does not make **owning** the tool cheap. The total cost of ownership
includes: who answers for the data it shows, keeping up with the APIs of the systems it reads, explaining a report that
is silently wrong, permissions and audit, uptime, onboarding new users. Replacing a SaaS product means taking over all of
that. So the question is not "can we build it?" but "do we want to own this?".

## Four directions
| Direction | Choose when | First step |
|---|---|---|
| **Buy / use what exists** | the problem is generic; an existing product or a built-in feature covers it | try the feature or a trial for two weeks |
| **Extend** (usually the best start) | the value comes from connecting several systems | a thin layer that reads, summarises and **links back to the sources** — it never becomes a new source of truth |
| **Build** a fuller flow | the extension has proved itself: people use it, it saves measurable time, it has an owner and a clear scope | requirements (proc-requirements-shaping) |
| **Wait / do not build** | the signal is weak, the problem is solved elsewhere, or the friction comes from a real constraint (approval, regulation) | name the existing tool to try instead |

## Qualifying the candidates
For each proposed tool fill one row:

| Friction signal | What existing tools already give | Thin extension | First useful version | Data risk | Direction if it proves itself |
|---|---|---|---|---|---|

- **Friction signal** — repeatable, observable, and not a solution: "the support lead spends about an hour every Friday
  copying ticket counts from the help desk, the CRM and the SLA spreadsheet into one e-mail", not "we need a dashboard".
- **Data risk** — mock, local, read-only or non-sensitive data → go light. Real company or customer data → access,
  permissions and audit are settled **before** implementation (arch-privacy-compliance).

Pick **at most one** candidate that: recurs; connects at least two sources or roles; has a visible manual cost; can be
checked on an export or read-only access; does not take over a platform's responsibilities; has a clear direction to grow.
If none passes, the answer is "do not build" plus the existing tool to try. A team maintains two or three small tools well;
ten prototypes compete for the same maintenance attention.

## Describe the first version in 5–8 sentences
What it reads, what it returns, what it does **not** do, the data risk, and the direction if it works.

## Grow in steps
Start with the cheapest form that answers the question, and move up only when the previous one is used:
1. a hand-written sample of the output (Markdown) shown to the people who would use it;
2. a script run on exported files (CSV, JSON);
3. a static page shared by hand;
4. only then a scheduled job, an agent or an application.

## When a tool turns into a product
Signals: people plan their day around its output; a wrong report causes confusion; people ask for sources, access control
or running without anyone watching. Then change its status on purpose: an owner, error handling, behaviour when data is
missing, a defined audience. Next step: a short conversation with the manager and the team, questions about past behaviour
(`.claude/skills/ddd-discovery-intake/references/user-research.md`), then requirements — or straight to a plan if the scope is narrow.

## Example
**Situation:** the support team wants an AI-built tool that every Friday collects ticket numbers from the help desk, the
CRM and the SLA spreadsheet into a report for the lead.
**Result:**
- Signal: about an hour each Friday for the lead; repeated every week; three sources.
- Existing tools: the help desk has a built-in weekly report, but without CRM account tiers or SLA breaches.
- Direction: **extend** — a script on the three exports that produces a one-page summary with links to the original
  tickets; it does not store tickets or change them.
- Data risk: ticket text contains customer data → the script reads only counts, ids and tiers; access through a read-only
  export.
- First version: a hand-written sample of the summary reviewed by the lead; then the script on last week's exports.
- If it proves itself (used four Fridays in a row, the hour drops to ten minutes): an owner in the team and a scheduled run.
