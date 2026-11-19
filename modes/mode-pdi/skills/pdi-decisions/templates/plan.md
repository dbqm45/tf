# Plan of change {CHG}

Cuts (TSK) — each delivers value on its own and ends with verification. Also add the cut keys to `tasks` in the header,
and the release line (R1 = MVP) and the flag — to `release.yaml` (the same values as in the columns below).

Kind: "slice" (value: "the user can …") or "foundation" (value: "(foundation) … is ready"). A foundation
must list in "Unblocks" the cuts of this change (TSK) that need it; a slice — literal requirement IDs in "Requirements"
(`US-02`, `FR-007`) or a verification. This is the cut plan's self-check; `decision_record.py check` and REL-008 in ci_for_sdlc
check it the same way.

| Slice | Kind | Release | Flag | Value | Requirements | Unblocks | Files | Verification |
|---|---|---|---|---|---|---|---|---|
| TSK-? | slice | R1 | — | the user can … | US-? | — | | <command and expected result> |

## Options considered

At least two options with pros, cons and cost; state the choice and the reason (N20; `arch-tech-selection` §3). Rejected
options go into the justification of decision B3 and the gate card (N11). `decision_record.py check` rejects a plan with one
option.

### Option A — <name>

- Pros: …
- Cons: …
- Cost: … (learning, complexity, maintenance)

### Option B — <name>

- Pros: …
- Cons: …
- Cost: …

**Choice:** Option <A/B> — <a reason referring to factors from `arch-quality-attributes` and to the domain>.

## Change targets (`targets`)

Measurable thresholds the change must meet before B4 (Z7b-1, DZ7). The architect proposes them here, the human
approves them at B3; ci_for_sdlc checks them (Z7b-1b). Write the same values into `release.yaml` under the `targets` key —
this document is for the human, the YAML file for machines. For an AI product evaluation thresholds are mandatory (DZ7).

| Name                       | Kind        | Threshold  | Tool      | Justification (factor / risk)             |
|----------------------------|-------------|------------|-----------|-------------------------------------------|
| changed-line coverage      | coverage    | >= 90%     | …         | … (N4)                                    |
| mutations of changed code  | mutation    | >= 70%     | …         | StrykerJS (JS/TS) or mutmut (Python); N4  |
| p95 for path X             | performance | <= 400ms   | …         | follows from an SLO of 99.5% in 28 days (optional) |
| <evaluation name>          | evaluation  | >= <score> | <dataset> | **required for an AI product (DZ7)**      |
