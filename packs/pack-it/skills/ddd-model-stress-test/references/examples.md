# Examples — model stress test

## 1. Margin per project: from the brief to the impact report
**Situation.** "A software house, a system for running client projects. Modules: `offers`, `projects`, `time-tracking`,
`invoicing`. Check whether the model will withstand what the board wants in a year. The board's metric: margin per project."

**How.**
1. **Metric** given by the human verbatim — "margin per project"; I do not change it and do not add my own.
2. **Brief** (`_blind/brief.md`) about the business: fixed-price and hourly quotes, penalties for delays, the bench between projects,
   a scale of 30 projects a year. Module names removed; the mirror and invariance tests pass.
3. **Generator** `blind-analyst` as a subagent: it gets only the metric, the brief path and the number of requirements (8). Every requirement
   has a Request, a Mechanism and a Basis. The human approves and freezes the set.
4. **Impact assessment** only now, with the inventory of module capabilities (`stress/modules.md`): uses / extends / gains /
   no place, the class by the upper bound, every row with a "why".

**Result** — a requirement from the generator (`_blind/requirements.md`):
```markdown
### R-3
Request: what if the business wanted to quote fixed-price projects with a risk reserve that depends on the type of client?
Mechanism: the reserve covers hour overruns → fewer projects with a negative result → a higher average margin.
Basis: brief, "Where we lose": "every third fixed price exceeds the hours budget".
```
A fragment of the report (`stress/project-margin.md`):

| Requirement | offers | projects | time-tracking | invoicing | Class | Why |
|---|---|---|---|---|---|---|
| R-1 alert when hours used > 80% of the budget | uses | extends | uses | — | local (1) | the budget lives in the project, hours are only read |
| R-3 risk reserve in a fixed price | extends | uses | — | extends | distributed (2) | the reserve changes the quote and the amount on the final invoice |
| R-5 bench cost added to projects | — | extends | extends | — | distributed (2) | time without a project has no owner today |
| R-7 margin bonus for the project manager | — | uses | — | uses | new module: 0 (+1 new) | remuneration — no module is a natural place |

Distribution of classes (8 requirements): local 3 · distributed 4 · new module 1. Summary per module: `projects` — 4 changes, 3 uses;
`invoicing` — 2 changes. No quality judgements; a note: "this set can be repeated on another decomposition".

## 2. The same set, two decompositions
**Situation.** "The architect proposes merging `time-tracking` with `projects` into one module `delivery`. Is it a better split?"

**How.**
1. I do not generate new requirements — I take the **frozen** set from example 1 (8 requirements).
2. I repeat only step 5 (the impact assessment) for variant B.
3. I show where each variant strains; I do not decide — the decision and the ADR belong to the human (ddd-strategic-analysis).

**Result**:

| Class | Variant A (4 modules) | Variant B (`delivery`) |
|---|---|---|
| local (0–1) | 3 | 5 |
| distributed (≥ 2) | 4 | 2 |
| new module | 1 | 1 |
| module with the most changes | `projects` (4) | `delivery` (6) |

An observation for the ADR: B localises R-5 and R-6, but concentrates 6 changes in one module — that is where the strain moves.
R-7 requires a new module in both variants.

## 3. A metric described by a solution and a brief that failed the mirror test
**Situation.** "Shake the shop's model. Metric: a faster orders API."

**How.**
1. "A faster API" is a solution, not a business number → reformulation **with the human** (gate); proposal:
   "time from order to delivery", the human confirms the wording.
2. The first version of the brief has the sections "Catalogue", "Cart", "Payments", "Shipping" — 1:1 with the modules → the mirror test fails.
3. I rewrite the brief around business activities and remove the warning verbs (*synchronises*, *sends*).
4. Invariance test: the brief would sound the same for a shop run with a notebook and a telephone.

**Result** — the change of the brief:

| Before (contains a solution) | After (the business) |
|---|---|
| "The Payments module synchronises the status with the operator and sends an event to Shipping." | "We pack the parcel only after the payment is confirmed; with a traditional bank transfer we wait 1.5 days on average." |
| "Shipping stores three couriers in the database." | "We work with three courier companies; one picks up parcels only until 14:00." |
| sections: Catalogue · Cart · Payments · Shipping | sections: Who buys and why · From the order to the parcel · Where we lose time and money · Vocabulary |
