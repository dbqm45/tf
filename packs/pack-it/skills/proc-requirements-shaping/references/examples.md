# Examples — requirements shaping


## 1. Brownfield: what each phase asks
| Phase | Greenfield asks | Brownfield asks |
|---|---|---|
| Problem | whose pain, when, what it costs | what exists, who uses it, what hurts, what must not break |
| Access | who logs in, roles | the current model and what changes in it |
| MVP | the first flow within budget | the smallest proof of improvement and its blast radius |
| Requirements | FR-NNN, stories | the same plus `Change: new|changed|kept` |
| Business rule | the decision the app makes | how the rule changes, or "no change to the domain rule" |
| Recording | brief + requirements | plus "Current system" and "Preserved behavior" |

## 2. Brownfield case: a waiting list for a tool-lending app
**Situation:** neighbours already lend tools through the app; popular tools are always out, and people ask the owner in
private messages. The change: a waiting list.

Grey areas offered in phase 3 (with a recommendation):
- Who may join? a) any member (recommended — simplest) b) only members who returned their last tool on time c) I don't know
- What happens when the tool comes back? a) the first person gets 24 h to confirm, then the next (recommended)
  b) everyone is notified, first to click wins c) the owner chooses d) I don't know

Recorded:
- `FR-007: A member can join the waiting list of a lent tool. Priority: must. Change: new`
- `FR-003: A member can borrow a free tool for up to 7 days. Priority: must. Change: kept`
- Business rule: "When a tool is returned, the app offers it to the earliest member on its waiting list for 24 hours
  before moving to the next one."
- Preserved behavior: borrowing a free tool works as today; an owner can still block a tool for themselves.
- Out of scope (MVP): priority for members with good history; waiting lists across several copies of the same tool.

## 3. A challenge round for one FR
`FR-007: A member can join the waiting list of a lent tool.`
Question: "What would have to be true for this requirement to do harm?"
1. one member joins every list and blocks popular tools for everyone else;
2. the 24-hour hold leaves a returned tool idle on a busy weekend;
3. owners lose control over who borrows their tools;
4. none.
The human picked 1 → recorded under FR-007: "at most 3 active waiting-list places per member" (a new FR, `Priority: nice`).

## 4. Two implementations of a vague adjective
Requirement: "Notifications about a returned tool must be fast and reliable."
- Implementation A: send a push message at the moment the return is confirmed; no retry.
- Implementation B: a job every 15 minutes sends e-mails and retries three times.
A member would see a difference (seconds vs up to 15 minutes; a lost message vs a retried one), so the requirement is
silent. Questions on the five classes and the answers recorded:

| Class | Decision | Verification | Owner |
|---|---|---|---|
| Scale | up to 200 returns a day | load test in CI | tech lead |
| Execution mode | the member is notified within 5 minutes of the return | test with a fake clock | product owner |
| Failure and retries | a failed notification is retried; after 1 hour the owner is told | integration test | tech lead |
| Permissions | only the member next in line sees the offer | access test | product owner |
| Migration | existing private-message requests are not converted | review point at release | product owner |

The 5-minute promise is broad and hard to undo once members rely on it → the product owner decides before code.

## 5. Lint output
Running the lint on a draft with an unfinished business rule, a mechanism in a quality requirement and an estimate over
budget (brief: budget 3 weeks, estimate 5 weeks, no cost acknowledgement):

```
Readiness: 3/4
  · missing: "Business rule" in one sentence (≤ 200 characters, ending with a period, no TODO)
docs/project/03-requirements/requirements.md:16 — AC-003 miejsce wykonania: "server-side" → describe behaviour visible from outside or move it to "For the stack decision"
MVP: estimate 25 days > budget 15 days — cost NOT acknowledged — propose cuts
✗ there are blocking problems
```

Exit code 1. Fixes: write the business rule as one sentence; rewrite line 16 as "a member learns about a returned tool
within 5 minutes"; propose cuts or record `- Cost acknowledged: <date>, <who> accepts <how much>` in the brief.
