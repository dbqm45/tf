---
name: ddd-model-stress-test
description: Use for testing a model's extensibility along a business metric — blind requirements, impact on modules.
metadata:
  review: "2027-10-17"
  catalog: "Use to check the extensibility of a model/decomposition along a business metric — a brief without a solution, requirements generated \"blind\" (an agent without insight into the architecture), an assessment of the impact on modules, a comparison of decompositions. Not for gathering requirements from a client or measuring coupling in code (ddd-connascence-analysis)."
  keywords: "czy model wytrzyma przyszłe wymagania, rozszerzalność, nowe wymagania, porównanie dekompozycji, wpływ zmian na moduły, will the model withstand future requirements, extensibility, new requirements, comparison of decompositions, impact of changes on modules"
---

# Model stress test ("shake the model")

The question: **how many modules must change when the business wants to improve its metric?** A good decomposition absorbs typical
changes locally. The test makes sense only when the requirements are invented by someone who **has not seen the architecture** — requirements
written with knowledge of the modules fit them by construction and prove nothing.

## Flow
1. **Metric** — from the human, verbatim (e.g. "margin per project", "time from order to delivery"). Never invent it.
   A metric described by a solution ("a faster API") you reformulate with the human into a business number. Gate.
2. **Business brief** (the main thread) → `docs/project/02-domain/_blind/brief.md`. A story about the **business**: what the company does and for whom,
   where it earns and takes risks, the rules of the game, what it can already do, the vocabulary, the scale. You read technical materials (the context map, modules) as
   a source of knowledge about the business, but you **remove their form**: `references/business-brief.md`. Two tests before release: the mirror test
   and the invariance test. Gate.
3. *(optional)* **Competitor review** → `docs/project/02-domain/_blind/competitors.md` (`references/competitor-digest.md`); the network only with consent.
4. **Blind requirements** — the `blind-analyst` agent (a fresh context, Read only; the `cleanroom_guard.py` hook in the `blind` profile
   lets it read only `docs/project/02-domain/_blind/**`). It gets: the metric, the paths to the brief/review, the number of requirements.
   In the brief for it **do not give** module names or paths outside `02-domain/_blind/`. Result → `02-domain/_blind/requirements.md`.
   Gate: the human approves and **freezes** the set.
5. **Impact assessment** (only now the architecture) → `docs/project/02-domain/stress/<metric>.md` (`references/change-impact.md`).

## A requirement from the generator
- **Request** ("what if the business wanted…"), **Mechanism** (the causal chain to the metric), **Basis** (a fact from the brief or an entry
  from the review). Without a basis → reject it or mark it `ambitious:`.
- A ban on solution vocabulary and on predicting what will change in the system.
- Different levers (rules, offer, prices, external pressure) and different ambition; at most 1/3 of the requirements from the competitor review.
- The generator reports gaps in the material instead of guessing.

## Result and use
- The distribution of classes: **local** (0–1 modules) · **distributed** (≥ 2) · **new module** (wins over the others).
- The same frozen set can be run against **another** decomposition (you repeat only step 5) — this is a fair comparison of
  boundary variants (ddd-strategic-analysis) and evidence for an ADR.
- No "good/bad" judgements — the report shows where the model strains; the human makes the decision.

## Isolation tightness
The hook guards files, but not content the agent gets in other ways: **the brief in the call** (only the metric and the paths), the project's `CLAUDE.md`
(loaded for every agent — do not describe the modules in it) and the brief itself (the mirror test). Always run the generator as
a subagent — in the main thread the isolation does not work.

## Cost
You make the brief and the competitor review once and use them for many metrics; the generator on the std model; write the inventory of module capabilities
once (`02-domain/stress/modules.md`) and reuse it.

## Example
**Situation:** "A software house, modules `offers`, `projects`, `time-tracking`, `invoicing`. The board's metric: margin per project."
**Result** (8 blind requirements, frozen; a fragment of the report):

| Requirement | Changed modules | Class | Why |
|---|---|---|---|
| R-1 alert at 80% of the hours budget | projects | local | hours only read |
| R-3 risk reserve in a fixed price | offers, invoicing | distributed | changes the quote and the final invoice |
| R-7 margin bonus for the manager | 0 (+1 new) | new module | no natural place |

Distribution: local 3 · distributed 4 · new module 1. No judgements — the human's decision.
More examples: `references/examples.md`.
