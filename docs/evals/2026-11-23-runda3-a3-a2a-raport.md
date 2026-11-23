# Skill evaluations — 2026-11-23 21:10

Runs: 36 · cost: $0.41 · passed: 8/36

Trigger = skill loaded for a question that belongs to it. False = loaded for a question of a neighboring skill. Content = checks of specific knowledge in the answer (also without a trigger).

| Skill | Model | Trigger | False | Content | Passed | Cost |
|---|---|---|---|---|---|---|
| be-business-app-patterns | haiku | 7/9 | 0/0 | 3/9 | 2/9 | $0.15 |
| be-business-app-patterns | haiku (without skills) | 0/9 | 0/0 | 5/9 | 0/9 | $0.07 |
| eng-repo-readiness | haiku | 7/9 | 0/0 | 6/9 | 6/9 | $0.14 |
| eng-repo-readiness | haiku (without skills) | 0/9 | 0/0 | 0/9 | 0/9 | $0.05 |

## Protocol: result or cost

Main result: tasks passed in full (the answer meets all criteria — the same measure in both arms). Trigger: skill loaded. The criteria average is a diagnostic. Cost per solved task covers all runs of the arm. Unstable: a scenario with differing results between repeats (--repeats). Holdout is the closed set — we do not tune to its questions. Noise band: the spread of the full-pass rate between repeats of the arm — a difference between arms smaller than the band is noise, not a result. Repeats: 3 — the band is indicative (more reliable from 5).

| Model | Arm | Set | Passed in full | Trigger | Criteria average | Cost | Cost per solved | Unstable | Noise band |
|---|---|---|---|---|---|---|---|---|---|
| haiku | with skills | tuning | 9/18 (50%) | 14/18 | 76% | $0.29 | $0.032 | 2 | 33% |
| haiku | without skills | tuning | 5/18 (28%) | — | 74% | $0.12 | $0.024 | 1 | 17% |

## Skill contribution

Share of trigger scenarios with correct content with and without skills (same checks), only scenarios with runs in both arms. The "with skill" arm counts only runs in which the skill was triggered; scenarios without a trigger are in the last column (a description or hint problem, not content). Contribution near zero: the model copes without the skill or the scenarios are too easy. One run is noise — repeat the measurement (--repeats 5) before deciding on a skill.

| Skill | Model | Scenarios | Content with skill | Content without skills | Contribution | Skill not triggered |
|---|---|---|---|---|---|---|
| be-business-app-patterns | haiku | 3 | 33% | 56% | -22% (within the noise band) | 0 |
| eng-repo-readiness | haiku | 3 | 67% | 0% | +67% | 0 |

## Passed without skills

Trigger scenarios that pass the content checks without skills on every model — they do not measure the skill's contribution; to be tightened or replaced with harder ones.

- `be-business-app-patterns` / rodo-przy-soft-delete

## Failed

- `be-business-app-patterns` / zmiana-statusu-masowa / haiku: missing: app/*.py lacks ['(?i)CREATE TABLE (IF NOT EXISTS )?\\w*(job|operation|batch|bulk)\\w*']; missing: app/*.py lacks ['(?s)audit\\.record\\([^)]{0,300}(count|total|affected|len\\(|changed|processed)']; missing: tests/test_bulk.py lacks ['(?i)resum|retry|twice|again|idempot|repeat'] — skills used: be-business-app-patterns
- `be-business-app-patterns` / impersonacja-supportu / haiku: did not trigger
- `eng-repo-readiness` / szkielet-bez-decyzji / haiku: error_max_turns: None — skills used: eng-repo-readiness
- `be-business-app-patterns` / zmiana-statusu-masowa / haiku: missing: app/*.py lacks ['(?i)CREATE TABLE (IF NOT EXISTS )?\\w*(job|operation|batch|bulk)\\w*']; missing: tests/test_bulk.py lacks ['(?i)resum|retry|twice|again|idempot|repeat'] — skills used: be-business-app-patterns
- `be-business-app-patterns` / impersonacja-supportu / haiku: missing: app/*.py lacks ['(?i)impersonat\\w*_id|impersonator|acting_as|on_behalf'] — skills used: be-business-app-patterns
- `be-business-app-patterns` / rodo-przy-soft-delete / haiku: missing: tests/test_crm.py lacks ['(?i)shipping_name'] — skills used: be-business-app-patterns
- `eng-repo-readiness` / szkielet-bez-decyzji / haiku: error_max_turns: None
- `be-business-app-patterns` / zmiana-statusu-masowa / haiku: missing: app/*.py lacks ['(?i)CREATE TABLE (IF NOT EXISTS )?\\w*(job|operation|batch|bulk)\\w*']; missing: app/*.py lacks ['(?i)idempot|request_id|job_id|operation_id|dedup'] — skills used: be-business-app-patterns
- `be-business-app-patterns` / rodo-przy-soft-delete / haiku: did not trigger
- `eng-repo-readiness` / szkielet-bez-decyzji / haiku: error_max_turns: None
- `be-business-app-patterns` / zmiana-statusu-masowa / haiku (without skills): did not trigger
- `be-business-app-patterns` / impersonacja-supportu / haiku (without skills): did not trigger
- `be-business-app-patterns` / rodo-przy-soft-delete / haiku (without skills): did not trigger
- `eng-repo-readiness` / szkielet-bez-decyzji / haiku (without skills): did not trigger
- `eng-repo-readiness` / generator-pada / haiku (without skills): did not trigger
- `eng-repo-readiness` / pomiar-od-klonu-do-zielonych / haiku (without skills): did not trigger
- `be-business-app-patterns` / zmiana-statusu-masowa / haiku (without skills): did not trigger
- `be-business-app-patterns` / impersonacja-supportu / haiku (without skills): did not trigger
- `be-business-app-patterns` / rodo-przy-soft-delete / haiku (without skills): did not trigger
- `eng-repo-readiness` / szkielet-bez-decyzji / haiku (without skills): did not trigger
- `eng-repo-readiness` / generator-pada / haiku (without skills): did not trigger
- `eng-repo-readiness` / pomiar-od-klonu-do-zielonych / haiku (without skills): did not trigger
- `be-business-app-patterns` / zmiana-statusu-masowa / haiku (without skills): did not trigger
- `be-business-app-patterns` / impersonacja-supportu / haiku (without skills): did not trigger
- `be-business-app-patterns` / rodo-przy-soft-delete / haiku (without skills): did not trigger
- `eng-repo-readiness` / szkielet-bez-decyzji / haiku (without skills): did not trigger
- `eng-repo-readiness` / generator-pada / haiku (without skills): did not trigger
- `eng-repo-readiness` / pomiar-od-klonu-do-zielonych / haiku (without skills): did not trigger
