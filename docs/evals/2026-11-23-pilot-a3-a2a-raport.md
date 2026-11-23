# Skill evaluations — 2026-11-23 19:19

Runs: 4 · cost: $0.06 · passed: 0/4

Trigger = skill loaded for a question that belongs to it. False = loaded for a question of a neighboring skill. Content = checks of specific knowledge in the answer (also without a trigger).

| Skill | Model | Trigger | False | Content | Passed | Cost |
|---|---|---|---|---|---|---|
| be-business-app-patterns | haiku | 0/1 | 0/0 | 0/1 | 0/1 | $0.02 |
| be-business-app-patterns | haiku (without skills) | 0/1 | 0/0 | 0/1 | 0/1 | $0.01 |
| eng-repo-readiness | haiku | 0/1 | 0/0 | 0/1 | 0/1 | $0.02 |
| eng-repo-readiness | haiku (without skills) | 0/1 | 0/0 | 0/1 | 0/1 | $0.01 |

## Protocol: result or cost

Main result: tasks passed in full (the answer meets all criteria — the same measure in both arms). Trigger: skill loaded. The criteria average is a diagnostic. Cost per solved task covers all runs of the arm. Unstable: a scenario with differing results between repeats (--repeats). Holdout is the closed set — we do not tune to its questions. Noise band: the spread of the full-pass rate between repeats of the arm — a difference between arms smaller than the band is noise, not a result. Without repeats there is no band — repeat the measurement (--repeats 5) before deciding on a skill.

| Model | Arm | Set | Passed in full | Trigger | Criteria average | Cost | Cost per solved | Unstable | Noise band |
|---|---|---|---|---|---|---|---|---|---|
| haiku | with skills | tuning | 0/2 (0%) | 0/2 | 67% | $0.04 | — | 0 | — |
| haiku | without skills | tuning | 0/2 (0%) | — | 67% | $0.02 | — | 0 | — |

## Failed

- `be-business-app-patterns` / usuwanie-projektu / haiku: did not trigger
- `eng-repo-readiness` / audyt-przejmowanego-repo / haiku: did not trigger
- `be-business-app-patterns` / usuwanie-projektu / haiku (without skills): did not trigger
- `eng-repo-readiness` / audyt-przejmowanego-repo / haiku (without skills): did not trigger
