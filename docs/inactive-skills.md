# Disabled skills

Skills that a measurement found redundant: the model answers just as well without the skill. **They are not removed.**
They stay in the repository and in the installation, but:
- the model does not load them on its own (`disable-model-invocation: true`), and the `skill_hint` hook does not
  suggest them;
- `build.py` removes them from the skill lists of roles, personas, shared agents, consultants and `always_skills`, and in
  the catalog (`.claude/catalog.md`) they are in a separate "Disabled skills" section; the overlay YAML files do not
  change;
- a person can invoke a skill by hand: `/<name>`;
- the `trigger` scenarios are in `tests/skill_evals/inactive/<skill>.json`; the main file keeps the `no-trigger`
  scenarios;
- active skills and agent prompts do not refer to them by name: `build.py check` warns about every such reference, and
  the `IN-11` test in `test_build.py` fails as long as a reference remains in the factory content.

When disabling another skill, remove the references to it: keep the topic and drop the name, or point to an active
skill.

A skill is disabled when its SKILL.md header has `disable-model-invocation: true` and `metadata.status: "inactive"`.

## How to re-enable a skill
1. In SKILL.md remove `disable-model-invocation: true` and `status: "inactive"`.
2. Move the scenarios from `tests/skill_evals/inactive/<skill>.json` back to `tests/skill_evals/<skill>.json`.
3. `python3 .tf/factory/skill_gate.py <skill>` and `python3 .tf/factory/build.py`.
4. Remove the row from this list and add the reason for the return (e.g. a new measurement with an advantage, a new
   factory rule in the content).
5. The references removed when disabling (commit from 2026-11-16) can be restored where the skill adds something again.

When it is worth bringing one back: the skill gained knowledge the models do not have (a factory rule, a fresh tool
version), or a measurement on Haiku or on the holdout showed an advantage.

## List

Measurement: 2026-11-16, Sonnet, with and without the factory skills (`--baseline`), `--isolated`, one run per
scenario, `trigger` tuning scenarios. Report: `docs/evals/2026-11-16-podejrzane-skille-podsumowanie.md`, raw results:
`docs/evals/2026-11-16-podejrzane-skille.jsonl`. The scenarios were written from the skills' content, so they favor
the skills; a lack of advantage even so is a strong signal of duplication.

"✓" = the answer meets all content checks.

| Skill | Overlay | Disabled | With skill | Without skill | Reason |
|---|---|---|---|---|---|
| `eng-algorithms-data-structures` | pack-it | 2026-11-16 | 2/2 | 2/2 | complexity, data structures: textbook knowledge |
| `fe-technical-seo` | pack-it | 2026-11-16 | 3/3 | 3/3 | robots.txt, hreflang, soft 404: the model knows it on its own |
| `ops-iac-terraform` | pack-it | 2026-11-16 | 2/2 | 2/2 | state locking, drift: the model knows it on its own |
| `pm-saas-metrics` | pack-it | 2026-11-16 | 4/4 | 4/4 | NRR, burn multiple, Rule of 40, LTV: the model knows it on its own |
| `proc-lean` | pack-it | 2026-11-16 | 2/2 | 2/2 | Little's law, WSJF: the model knows it on its own |
| `tool-nx` | pack-it | 2026-11-16 | 3/3 | 3/3 | module boundaries, Nx 23 migration: the model knows it on its own, including the new version |
| `eng-design-patterns` | pack-it | 2026-11-16 | 2/3 | 3/3 | worse with the skill (`dekorator-vs-proxy`) |

### Results per scenario

| Skill | Scenario | With skill | Without skill | Skill loaded |
|---|---|---|---|---|
| eng-algorithms-data-structures | `kolejka-shift` | ✓ | ✓ | yes |
| eng-algorithms-data-structures | `top-k-sortowanie` | ✓ | ✓ | yes |
| fe-technical-seo | `robots-txt-a-indeks` | ✓ | ✓ | yes |
| fe-technical-seo | `sklep-jezyki-i-filtry` | ✓ | ✓ | yes |
| fe-technical-seo | `spa-soft-404-i-dane-produktu` | ✓ | ✓ | yes |
| ops-iac-terraform | `blokada-stanu` | ✓ | ✓ | yes |
| ops-iac-terraform | `dryf-i-ochrona` | ✓ | ✓ | yes |
| pm-saas-metrics | `burn-multiple-rule-of-40` | ✓ | ✓ | yes |
| pm-saas-metrics | `edge-ltv-bez-danych` | ✓ | ✓ | yes |
| pm-saas-metrics | `nrr-maskuje-churn` | ✓ | ✓ | yes |
| pm-saas-metrics | `zdrowie-ekonomiki` | ✓ | ✓ | yes |
| proc-lean | `prawo-little` | ✓ | ✓ | yes |
| proc-lean | `wsjf-priorytet` | ✓ | ✓ | yes |
| tool-nx | `bez-plikow-granice` | ✓ | ✓ | yes |
| tool-nx | `granice-modulow` | ✓ | ✓ | yes |
| tool-nx | `migracja-nx23` | ✓ | ✓ | yes |
| eng-design-patterns | `dekorator-vs-proxy` | ✗ (missing: "nie dubluj tego, co już robi" — "do not duplicate what it already does") | ✓ | yes |
| eng-design-patterns | `role-object` | ✓ | ✓ | yes |
| eng-design-patterns | `switch-strategia` | ✓ | ✓ | yes |

## Measured but not disabled

| Skill | With skill | Without skill | Why it stays |
|---|---|---|---|
| `eng-design-principles` | 2/3 | 2/3 | a tie from two different scenarios: with the skill it passes `agent-przeinzynierowuje-mimo-regul` (the factory rule "minimalism ladder"; without the skill ✗), without the skill it passes `dry-przypadkowe`; the skill is in `always_skills` of every pack-it persona |

## Limitations
- Sonnet only: Haiku without the skill may do worse. Cheaper executors (tier `fast`) also lose these skills.
- One run per scenario; tuning scenarios, not a holdout.
