# Skill evaluations — 2026-11-20 20:45

Runs: 2 · cost: $0.29 · passed: 2/2

Trigger = skill loaded for a question that belongs to it. False = loaded for a question of a neighboring skill. Content = checks of specific knowledge in the answer (also without a trigger).

| Skill | Model | Trigger | False | Content | Passed | Cost |
|---|---|---|---|---|---|---|
| ddd-archetypes | haiku | 1/1 | 0/0 | 1/1 | 1/1 | $0.14 |
| ddd-archetypes | sonnet | 1/1 | 0/0 | 1/1 | 1/1 | $0.14 |

## Protocol: result or cost

Main result: tasks passed in full (the answer meets all criteria — the same measure in both arms). Trigger: skill loaded. The criteria average is a diagnostic. Cost per solved task covers all runs of the arm. Unstable: a scenario with differing results between repeats (--repeats). Holdout is the closed set — we do not tune to its questions. Noise band: the spread of the full-pass rate between repeats of the arm — a difference between arms smaller than the band is noise, not a result. Without repeats there is no band — repeat the measurement (--repeats 5) before deciding on a skill.

| Model | Arm | Set | Passed in full | Trigger | Criteria average | Cost | Cost per solved | Unstable | Noise band |
|---|---|---|---|---|---|---|---|---|---|
| haiku | with skills | tuning | 1/1 (100%) | 1/1 | 100% | $0.14 | $0.142 | 0 | — |
| sonnet | with skills | tuning | 1/1 (100%) | 1/1 | 100% | $0.14 | $0.143 | 0 | — |
