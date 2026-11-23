# Skill evaluations — 2026-11-23 19:34

Runs: 12 · cost: $0.17 · passed: 6/12

Trigger = skill loaded for a question that belongs to it. False = loaded for a question of a neighboring skill. Content = checks of specific knowledge in the answer (also without a trigger).

| Skill | Model | Trigger | False | Content | Passed | Cost |
|---|---|---|---|---|---|---|
| be-business-app-patterns | haiku | 3/3 | 0/0 | 3/3 | 3/3 | $0.06 |
| be-business-app-patterns | haiku (without skills) | 0/3 | 0/0 | 0/3 | 0/3 | $0.02 |
| eng-repo-readiness | haiku | 3/3 | 0/0 | 3/3 | 3/3 | $0.06 |
| eng-repo-readiness | haiku (without skills) | 0/3 | 0/0 | 0/3 | 0/3 | $0.03 |

## Protocol: result or cost

Main result: tasks passed in full (the answer meets all criteria — the same measure in both arms). Trigger: skill loaded. The criteria average is a diagnostic. Cost per solved task covers all runs of the arm. Unstable: a scenario with differing results between repeats (--repeats). Holdout is the closed set — we do not tune to its questions. Noise band: the spread of the full-pass rate between repeats of the arm — a difference between arms smaller than the band is noise, not a result. Repeats: 3 — the band is indicative (more reliable from 5).

| Model | Arm | Set | Passed in full | Trigger | Criteria average | Cost | Cost per solved | Unstable | Noise band |
|---|---|---|---|---|---|---|---|---|---|
| haiku | with skills | tuning | 6/6 (100%) | 6/6 | 100% | $0.12 | $0.020 | 0 | 0% |
| haiku | without skills | tuning | 0/6 (0%) | — | 58% | $0.05 | — | 0 | 0% |

## Skill contribution

Share of trigger scenarios with correct content with and without skills (same checks), only scenarios with runs in both arms. The "with skill" arm counts only runs in which the skill was triggered; scenarios without a trigger are in the last column (a description or hint problem, not content). Contribution near zero: the model copes without the skill or the scenarios are too easy. One run is noise — repeat the measurement (--repeats 5) before deciding on a skill.

| Skill | Model | Scenarios | Content with skill | Content without skills | Contribution | Skill not triggered |
|---|---|---|---|---|---|---|
| be-business-app-patterns | haiku | 1 | 100% | 0% | +100% | 0 |
| eng-repo-readiness | haiku | 1 | 100% | 0% | +100% | 0 |

## Failed

- `be-business-app-patterns` / usuwanie-projektu / haiku (without skills): did not trigger
- `eng-repo-readiness` / audyt-przejmowanego-repo / haiku (without skills): did not trigger
- `be-business-app-patterns` / usuwanie-projektu / haiku (without skills): did not trigger
- `eng-repo-readiness` / audyt-przejmowanego-repo / haiku (without skills): did not trigger
- `be-business-app-patterns` / usuwanie-projektu / haiku (without skills): did not trigger
- `eng-repo-readiness` / audyt-przejmowanego-repo / haiku (without skills): did not trigger
