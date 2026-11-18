# Report format (`docs/project/02-domain/algorithms.md`)

The artifact header per core-project-record (`artifact: algorithms`, `phase: domain`, `inputs: [areas.md, corpus.md]`).

## Per area
```markdown
## A2 — Planning project stages
| Candidate | Basis (track) | Confidence | Quotes |
|---|---|---|---|
| job-scheduling | language + structural | high | E12 S1 L40 "a 2% penalty per week of delay"; E30 S2 track: PM/4 |
| topological-sort | structural | medium | E31 S2 track: PM/2 |

**Mapping (job-scheduling):** node = stage; edge = "stage B requires the results of A" (E31); weight = the stage duration (E33);
deadline = the date from the contract (E12); shared resources = implicit edges (E35).
**Variants:** a schedule with limited resources → an NP-hard problem (E35: "the same specialist in two stages").
**Confidence justification:** both tracks, different quotes, 4 mapping elements.
**Best candidate:** job-scheduling.
```

## At the end
- **Honest gaps:** word/quote → why the catalogue does not fit.
- **Observations across areas:** consolidation / shared kernel / seam — with a justification.
- TL;DR, Open questions, Handoff (for ddd-strategic-analysis and arch-tech-selection).
