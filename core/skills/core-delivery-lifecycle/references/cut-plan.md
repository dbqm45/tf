# The cut plan — the order of work before the plan of the first step

> **Contents:** Two kinds of items · Item fields · Order · Release lines and flags · Slice size (no estimates) · Unknowns — where to settle them · Self-check before saving · Handoff

The cut plan (`docs/project/05-plan/plan.md`, the `plan` template in core-project-record) answers only these questions:
what first, what depends on what, what is blocked and what we postpone. It does not choose frameworks, does not design
the schema and does not list files — the step plan in the `06-delivery/` report does that.

The plan's column names stay in their template form (e.g. `Odblokowuje`, `Wymagania`), because `decision_record.py`
and the pdi contract read them; below each one has its meaning next to it.

## Two kinds of items
- **S-NN — a slice:** one capability visible to the user, going through all the layers it needs. The result starts with
  "the user can …". If that sentence cannot be written, it is not a vertical slice.
- **F-NN — a foundation:** the smallest preparatory work without its own effect for the user. It must have the
  **`Odblokowuje`** (unblocks) field: a specific S-NN, a specific unknown to settle or a verification path that an S-NN
  needs. A foundation without `Odblokowuje` is layered work — remove it or fold it into the first slice that needs it.
- **The limit of a foundation:** it does not finish a whole layer ("the whole data model", "the whole API", "full
  authentication"). After it is done, at least one S-NN still integrates that layer through a real feature.
- **A technical element appears in the first slice that needs it.** A foundation makes sense only when without it the
  first slice cannot be planned, secured or checked.
- A foundation does not duplicate a layer that the **repository inventory** reports as present. The inventory: frontend,
  backend/API, data, authentication, deployment, observability — each as present / partial / missing, with a file as
  evidence (a code map; pack-it: eng-codebase-mapping).
- A justified "horizontal first" (an integration with a legacy system, a regulatory requirement for the data model, a
  performance-critical core) is still an F-NN: specific, bounded and pinned to an S-NN.

## Item fields
| Field (column) | Rule |
|---|---|
| `Wynik` (outcome) | S: "the user can …", F: "(foundation) … is ready" |
| `Identyfikator zmiany` (change identifier) | kebab-case, stable; the name of the branch and of the step report (not `S-01`) |
| `Wymagania` (requirements) | literal IDs from the requirements (`FR-007`, `US-02`), no paraphrase |
| `Warunki wstępne` (preconditions) | IDs of other items or a specific external state |
| `Równolegle z` (in parallel with) | items with no dependency path between them (separate worktrees — core-git-workflow) |
| Blockers | only external ones (a vendor, a stakeholder's decision); what the team settles itself is an unknown |
| Unknowns | a question — an owner — blocks: yes/no |
| Risk | one sentence: why the item stands exactly here in the order |
| `Wydanie` (release) | the release line: `R1` (MVP), `R2`… — the "Release lines and flags" section |
| `Flaga` (flag) | the key of the flag behind which the slice is deployed before the decision to expose it, or "—" |
| `Status` | proposed / ready / blocked / in progress / done |

- **Blocked** if and only if at least one unknown has "blocks: yes".
- **Ready** only when all preconditions are done (or present in the inventory) and there are no blocking unknowns.

## Order
1. Foundations in dependency order, then slices — nothing depends on a later item (topological order).
2. **The north star** — the smallest end-to-end flow that proves the product thesis — as early as the dependencies
   allow. It does not have to be first.
3. Ties are settled by the **sequence goal** recorded in the plan:
   - a fast release → the "must" path first, the rest postponed;
   - a market signal → the riskiest assumption first;
   - quality → security and observability foundations are not postponed;
   - learning → the unknown technology first;
   - simplicity → the smallest slice first.
4. An open question that affects the order leaves the affected items blocked — do not presume the answer.

## Release lines and flags
- **R1 = MVP:** the north star plus the minimum that gives the outcome from the change's intent (`intent.md`) or from the
  goals in the brief. It has a named outcome and a metric with a threshold and a horizon ("recovered payments ≥ 25% in
  30 days") and guardrail metrics. The rest goes to R2…Rn; "Out of MVP scope" from the requirements are candidates for R2.
- **A flag** when a slice is deployed before the human decides to expose it: an owner, a removal date and rollout stages
  (internal → percent → 100%), each with an exit criterion and a minimum time.
- The record: the release plan `release.yaml` next to the cut plan (`05-plan/release.yaml`; a change in the change log:
  `changes/CHG-n/release.yaml`) in the shape of the pdi 0.4.0 contract:
  ```yaml
  change: CHG-12
  mvp:
    release: R1
    outcome: The customer can retry a failed payment without being charged twice
    metric: { name: recovered_payments, target: ">= 25%", horizon_days: 30 }
    guardrails: [double_charges = 0]
  releases:
    - { id: R1, name: MVP, tasks: [TSK-57, TSK-58] }
    - { id: R2, tasks: [TSK-59] }
  flags:
    - key: payment-retry
      tasks: [TSK-57, TSK-58]
      owner: PO Payments
      remove_by: 2026-12-31
      rollout:
        - { stage: internal, min_days: 3, exit: "0 critical bugs" }
        - { stage: "10%", min_days: 7, exit: "recovered >= 15%, duplicates = 0" }
        - { stage: "100%" }
  ```
  The `Wydanie` and `Flaga` columns in the plan have the same values as `release.yaml`.

## Slice size (no estimates)
Slices have a comparable weight. Split a slice when it:
- covers more than one main user action;
- combines configuration, the main flow and administration;
- covers most of the "must" requirements while other slices cover one minor each;
- has more than one independent risk or unknowns of different owners.
Split by narrower outcomes (process paths, personas, stages), never by layers. The cut plan has no days, points or
sizes — the order comes from the dependencies. Cost and deadline for the sponsor: separately, as ranges (project
planning; pack-it: proc-project-planning).

## Unknowns — where to settle them
| Kind of unknown | Where |
|---|---|
| local, about the code ("is there already a form component?") | the step plan — it checks the repo and decides |
| external, affects a technical decision (a library, a vendor API, an algorithm) | research before the step plan (core-source-research; pack-it: eng-codebase-mapping) |
| a suspicious assumption, the problem may be framed wrongly | reframing before the step plan (pack-it: eng-debugging) |
| no effect on the current slice | "Open questions" or "Postponed" |
Research makes sense when it blocks a decision — not "just in case".

## Self-check before saving
Do not save the plan if any point fails:
- [ ] every "must" requirement and every story appears in the `Wymagania` field of at least one slice;
- [ ] every slice has at least one real requirement ID — a new need from the conversation goes to "Open questions" or
      "Postponed", not into the plan;
- [ ] the graph has no cycles, every ID from the preconditions exists, the order is topological;
- [ ] every F-NN has `Odblokowuje`, does not finish a whole layer and does not duplicate a layer present in the inventory;
- [ ] statuses agree with the unknowns; the table agrees with the item descriptions;
- [ ] at least one slice is "ready" — if everything is blocked or there are five F and zero ready S, the requirements
      are not closed or the inventory was misread: go back to phase 3;
- [ ] the terms "north star" and "riskiest assumption" explained in one sentence at first use (the human does not know
      the plan's jargon);
- [ ] R1 has an outcome and a metric (threshold, horizon) from the change's intent; every S-NN in R1 is visible to the user;
- [ ] every S-NN deployed before the decision to expose it has a flag with an owner, a removal date and stages with an
      exit criterion; `release.yaml` agrees with the `Wydanie` and `Flaga` columns.

## Handoff
At the end **one** recommendation of the next step, not a list to choose from: the north star, if ready; otherwise the
foundation that unblocks it; otherwise the most important unknown to settle; otherwise the ready slice with the most
dependent items. Before the step plan it is worth reviewing the plan (change review; pack-it: qa-change-review, mode A).

Source: the 10xDevs course, ed. 3 (2026), module 2, lessons 1–2 (roadmap, unknowns) — training material
(accessed 2026-10-09); A. Cockburn — walking skeleton. Described in our own words.
