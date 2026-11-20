# Worked examples

## 1. Mechanical rename across 12 files
Task: rename `customerRef` to `accountRef` in the orders module; module tests and the type check cover the usages.
- Assessment: checkable by command (yes), easy to undo (yes), no decision, no sensitive area, one pattern -> lowest tier.
- Brief: `Class: mechanical`, `quick-fixer` with `model: haiku`, the list of files from `rg -l customerRef src/orders`, done =
  module tests + type check green.
- First attempt misses a serializer; tests fail. Second attempt with the failing output fixes it. Had it failed twice, the
  next call would go to sonnet with both failure outputs in the brief.

## 2. Flaky payment due-date test after two failed fixes
- Two sonnet attempts "fixed" the test by widening a tolerance; the flake returned. Verification failed twice -> escalate one
  level: `Class: decision`, opus, the brief lists what was tried and why it did not hold.
- Opus finds the cause (the test builds a date in local time, the code in UTC across a month boundary) and returns a
  diagnosis only. Implementation goes back to sonnet with the diagnosis and a new test pinned to a fixed clock.
- The first executor ends its report with `Tier: too low — date/timezone reasoning`; the cost report later suggests raising
  that role's tier for date-handling tasks.

## 3. Reading a costly week
`python3 .tf/factory/cost_report.py --days 7` and `python3 .tf/factory/cost_stats.py --period week` show the week in the
"expensive" band against earlier weeks. Look for patterns, then propose one configuration change per finding:

| Finding | Evidence | Change |
|---|---|---|
| Executors often report `Tier: too high` | `.tf/logs/delegation.jsonl`, 9 reports for `mechanical` | Lower that role's tier in `.tf/config/config.yaml` |
| Cold cache after lunch breaks | status line "cold", long re-reads at 13:00 | Resume from a checkpoint in a new session after breaks |
| `/model` switched mid-task | cost spikes right after the switch | Pick model at session start; delegate the hard step instead |
| `quality` profile on short tasks | profile log | Default to `balanced`; switch to `quality` per task |

No logs for part of the week -> the statistics show "incomplete data"; say which days are missing instead of estimating.
