# Cut plan — vertical slices with enabling work (phase 5)

> **Contents:** 1. Inputs · 2. Two kinds of item · 3. Choosing the first slice and the order · 4. Table columns (fixed) · 5. Status and blocking unknowns · 6. Slice size · 7. Release lines and flags (`release.yaml`) · 8. Self-check before B3 · 9. Handoff · 10. Example · 11. Sources

The cut plan turns accepted requirements (B2) and the architecture into an ordered list of deliverable items in
`05-plan/plan.md` (template `plan` in core-project-record). Its job is to make the first useful result arrive early
and to keep every item small enough to review. The method combines the walking skeleton (Cockburn), story mapping
(Patton) and testing the riskiest assumption first (Ries).

## 1. Inputs
- `03-requirements/requirements.md` with requirement IDs and acceptance criteria; the spec review result if one ran.
- `04-architecture/stack-decision.md` and ADRs.
- What already exists in the repository — the plan's **Repository inventory** table: each layer (UI, API, domain,
  storage, pipeline, deployment, observability) marked present / partial / missing with a file as evidence. In a
  brownfield project this stops the plan from scheduling work that is already done.

## 2. Two kinds of item
| Kind | ID | What it delivers | Must name |
|---|---|---|---|
| Vertical slice | `S-NN` | a behaviour a user (or calling system) can exercise end to end: "the user can …" | at least one real requirement ID (e.g. `FR-007`, `US-02`, `TSK-57`) or, where no ID exists, a verification |
| Foundation (enabling work) | `F-NN` | something no user sees but slices need: a pipeline, an auth adapter, a schema migration framework | the slices of **this** change it unblocks, in `Odblokowuje (F)` |

Rules:
- A foundation with an empty Unblocks cell is layered work in disguise — drop it or fold it into the first slice that
  needs it. Unblocks entries must be items of the same change.
- A foundation is as small as the first slice needs; it grows with later slices, not ahead of them.
- "Build the whole data model first", "all the endpoints, then all the screens" are layered plans: each slice adds the
  tables, endpoints and screens its own behaviour needs.

## 3. Choosing the first slice and the order
1. **North star** (heading kept for the template and the plan check): the thinnest end-to-end flow that proves the
   product works at all — one user action through every layer, deployed to a test environment. Write it in one
   sentence with its item ID. It doubles as the walking skeleton.
2. **Riskiest assumption next:** the item whose failure would change the plan most (an external API, a performance
   limit, a regulatory constraint) goes as early as dependencies allow, or gets a spike first.
3. **Dependencies:** an item starts only when its `Warunki wstępne` are done; `Równolegle z` shows what can run at the
   same time on separate branches.
4. **Tie-break** when several orders satisfy 1–3: the front-matter key `cel_sekwencji` states what the sequence
   optimises — `fast release`, `market signal`, `quality`, `simplicity` or `learning` — and the order that serves it
   best wins. `glowne_ryzyko` (`decisions | time | throughput | external | skills | none`) names the main threat to the
   plan; it tells you where to put spikes and buffers (e.g. `external` → integrate the third party early behind a stub).

## 4. Table columns (fixed)
The items table in the template (column names are read by `decision_record.py` and the pdi contract; do not rename them):

`ID` | `Identyfikator zmiany` | `Wynik (użytkownik może …)` | `Wymagania` | `Warunki wstępne` | `Odblokowuje (F)` |
`Równolegle z` | `Wykonawca` | `Status`, plus `Wydanie` and `Flaga` when a release plan exists.

The mode-pdi plan template uses the English names `Release`, `Flag`, `Unblocks`, `Requirements`, `Verification`.
The values in `Wydanie`/`Release` and `Flaga`/`Flag` must equal those in `release.yaml`.

Other template sections: **North star**, **Repository inventory**, **Blocking unknowns**, **Spikes**, **Postponed**,
**Done**, then Open questions and Handoff.

## 5. Status and blocking unknowns
Status values: `proposed` / `ready` / `blocked` / `in progress` / `done`.
- `blocked` exactly when the item depends on an open question marked Blocks = yes in **Blocking unknowns**.
- `ready` only when every precondition is `done` and no blocking unknown points at it.

How to treat an open question:
| Situation | Action |
|---|---|
| The answer changes what is built, and only a person can give it (business rule, legal, budget) | Blocking unknown with an owner; the dependent items are `blocked` |
| The answer can be found by trying (does the library handle X, is the API fast enough) | A time-boxed spike in **Spikes**, result recorded, then the item becomes `ready` |
| A reasonable default exists and is cheap to change later | Proceed with the default, write it in `decisions.md`, Blocks = no |
| Not needed for the next release line | Move the item to **Postponed** with the reason |

## 6. Slice size
A slice should be reviewable in one sitting and demonstrable with one acceptance example. Split it when:
- it contains several user actions that could ship separately (split by workflow step);
- it mixes the happy path with many error or edge paths (ship the happy path, then the rules one by one);
- it serves several data variants or user roles that differ in behaviour (one variant first);
- it carries more than one independent technical risk (separate the risks, or spike one);
- its requirements are only partly covered (split off the covered part, leave the rest with its own ID).
Do not split below the point where a slice no longer changes anything a user or caller can observe.

## 7. Release lines and flags (`release.yaml`)
Group slices into release lines. **R1 is the MVP**: the North star plus the minimum needed for a measurable outcome.
Write the plan to `05-plan/release.yaml` (or `changes/CHG-n/release.yaml`):

```yaml
change: CHG-12
mvp:
  release: R1
  outcome: "customers recover failed card payments without contacting support"
  metric: {name: recovered_payment_rate, target: ">= 30%", horizon_days: 30}
  guardrails: ["refund rate does not rise", "p95 checkout latency < 800 ms"]
releases:
  - {id: R1, name: MVP, tasks: [F-01, S-01, S-02]}
  - {id: R2, tasks: [S-03, S-04]}
flags:
  - key: payment-retry
    tasks: [S-01, S-02]
    owner: product-owner
    remove_by: 2027-03-31
    rollout:
      - {stage: internal, min_days: 3, exit: "no P1 defects"}
      - {stage: "10%", min_days: 7, exit: "metric trend positive, guardrails green"}
      - {stage: "100%"}
```

- Every slice belongs to exactly one line; a slice sits behind at most one flag.
- Every flag has an owner, a `remove_by` date and rollout stages (internal → percentage → 100%).
- Phase 8 follows these stages; each move to the next stage is human gate **B5**.

## 8. Self-check before B3
- [ ] The North star is one sentence, names an item, and crosses every layer.
- [ ] Every `F-NN` has an Unblocks value naming slices of this change.
- [ ] Every `S-NN` has a real requirement ID or a verification.
- [ ] No item is `ready` while a precondition is open or a blocking unknown points at it.
- [ ] Every blocking unknown has an owner; spikes have a time box.
- [ ] No layered items ("all tables", "all APIs").
- [ ] Release and Flag cells match `release.yaml`; R1 has an outcome metric with a target and horizon.
- [ ] Postponed items carry a reason.

`decision_record.py` in mode-pdi checks the foundation and requirement rules automatically.

## 9. Handoff
The Handoff names **one** recommended next item (the first `ready` one in order), the persona that delivers it and what to
read (TL;DR, North star, that item's row). Alternatives, if any, go to Open questions — the delivering persona should
not have to choose.

## 10. Example
14 requirements for a booking app; the payment provider's sandbox terms are not yet confirmed.

| ID | Wynik (użytkownik może …) | Wymagania | Warunki wstępne | Odblokowuje (F) | Status |
|---|---|---|---|---|---|
| F-01 | — (pipeline to test env, health check) | — | — | S-01, S-02 | ready |
| S-01 | see free slots for one resource and book one | FR-001, FR-002 | F-01 | — | proposed |
| S-02 | cancel own booking | FR-005 | S-01 | — | proposed |
| F-02 | — (payment adapter stub) | — | S-01 | S-04 | blocked |
| S-04 | pay a deposit when booking | FR-009 | F-02 | — | blocked |

North star: S-01. Blocking unknown "which payment provider and contract" (owner: product owner, Blocks = yes) → F-02 and
S-04 are blocked; the rest proceeds.

## 11. Sources
- Alistair Cockburn, *Crystal Clear* (2004) — walking skeleton.
- Jeff Patton, *User Story Mapping* (2014) — slicing by user activity, release lines across the map.
- Eric Ries, *The Lean Startup* (2011) — test the riskiest assumption first.
- Pete Hodgson, "Feature Toggles (aka Feature Flags)", martinfowler.com (2017) — flag lifecycle and removal.
