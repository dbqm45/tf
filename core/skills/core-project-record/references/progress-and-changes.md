# Progress checklist, spikes, decisions and changing accepted work

## 1. The `### Progress` checklist of a step report
The step plan in `06-delivery/NNN-<slug>.md` lists phases with automatic and manual criteria. The checklist under
`### Progress` mirrors those criteria and is the only place in the report with checkboxes, so a script or a fresh session
can find the position without reading prose.

Rules — the same idea as a stable issue number or an ADR number: an ID, once given, means one thing forever.
| Situation | What you write |
|---|---|
| item finished | `[x]` immediately, not at the end of the phase |
| phase committed | append ` — <sha>` to the last item of that phase, once |
| item dropped | leave it unchecked with `(dropped: <reason>)`; the number is not reused |
| intent changed | keep the title, add `(changed: <what>, <date>)` |
| new item mid-phase | next free number in that phase, e.g. `2.4` after `2.3` |
| manual criterion | tick only after the human confirms, write who and when |

Derived values:
- next step = first `[ ]`, current phase = its phase prefix;
- completion = ticked / all items (dropped items count as neither);
- before closing the last phase, list every unticked manual criterion from earlier phases and ask the human about each.

### Worked example
A three-phase change adding CSV export to an invoices list, two phases committed:
```
### Progress
#### Phase 1: Query and serializer
- [x] 1.1 `pytest tests/export/test_rows.py` passes
- [x] 1.2 10 000 rows serialize in < 2 s (`pytest -k perf`) — 5e3a1c0
#### Phase 2: Endpoint
- [x] 2.1 GET /invoices/export returns text/csv
- [ ] 2.2 auth: 403 for role viewer (dropped: viewers may export, decision D-014)
- [x] 2.3 filename contains the date — 91bd7f2
#### Phase 3: UI button
- [ ] 3.1 button visible on the list (manual)
- [ ] 3.2 Playwright test `export.spec.ts` passes
```
Next step: 3.1, current phase 3, completion 4/6 (the dropped 2.2 is left out; six live items, four ticked).
Phase 3 has no SHA yet because it is not committed. 3.1 is manual: the agent prepares the build and asks the
human to look; it is not ticked on a passing test.

## 2. Spikes and other investigations
When the outcome is knowledge (which caching library, why latency doubled, whether an API supports X), write a separate
report — a time-boxed spike in the XP sense — never an appendix to a delivered change:
- **Question and scope** on top: what is studied, the time box.
- **Not doing:** what is deliberately out (no code merged, no benchmark on production data, …).
- **Decider:** who chooses and by when; the report ends with options, not with a decision taken for them.
- Location: a new step report in `06-delivery/` or a review in `07-review/<date>-<kind>.md`, whichever the plan uses.
A closed change stays closed; if the spike leads to work, the plan gets a new item.

## 3. Who decided what
Step reports and reviews keep `## Human decisions vs AI proposals` — a small decision log with the decider and the reason:
| Agent's proposal | Human's decision | Why |
|---|---|---|
| retry 3 times with fixed delay | 5 times, exponential backoff | provider rate-limits bursts |
Durable decisions also go to `decisions.md`; the table shows the moments where the human overrode or confirmed the agent.

## 4. Changing an accepted artifact
1. Copy the current file to `docs/project/archive/<name>-v<N>.md`, set `status: superseded`, `superseded_by: <path of the new one>`.
2. In the live file raise `version` to N+1, status `proposed`, update `updated`, describe the change in the TL;DR.
3. Add a decision row if the change reverses an earlier decision (mark the old row superseded, do not delete it).
4. `log` the change, `check`, and ask for acceptance again.
Typos and broken links may be fixed without a new version; anything that changes meaning may not.
