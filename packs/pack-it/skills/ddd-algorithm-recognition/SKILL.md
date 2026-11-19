---
name: ddd-algorithm-recognition
description: Use when an algorithmic problem hides in the domain — assignment, ordering, packing, routes, collisions in time.
metadata:
  review: "2027-10-17"
  catalog: "Use when you look for a hidden classic algorithmic problem in a domain area (ordering and dependencies, assignment, packing into limits, coverage, routes, collisions in time, similarity) — two matching tracks, domain→algorithm mapping, confidence, report. Not for the problem class (ddd-deep-modeling) or choosing libraries (arch-tech-selection)."
  keywords: "znany problem algorytmiczny, harmonogram etapów, zależności między etapami, równolegle, kara za opóźnienie, ścieżka krytyczna, kolejkowanie zadań, przydział, plan tras, pakowanie, known algorithmic problem, stage schedule, dependencies between stages, in parallel, delay penalty, critical path, task queuing, assignment, route plan, packing"
---

# Recognizing algorithmic problems in the domain

Under the business language there is often a problem solved long ago ("a stage plan with dependencies" = topological sort
and the critical path; "pick people for projects within a budget" = a multidimensional knapsack). Recognition gives you as an inheritance
**complexity, known pitfalls and ready solvers**. No match is also information: it is probably a novel core
(core, the left side of Cynefin — bottom-up analysis).

**The scan points to candidates, it does not make decisions.** It does not choose a tactical pattern, does not set boundaries, does not implement.
First confirm the problem class (ddd-deep-modeling): a simple CRUD does not need a solver.

## Two matching tracks — the result is the UNION, not the intersection
1. **Language track** — bridge words (nouns, verbs, adjectives: "depends on", "assign", "must not overlap",
   "cheapest", "queue", "similar") matched **by meaning**, in any language, to the families in `references/`.
2. **Structural track** — for each area, answer the questions about the shape of the problem:
   | Question | Family |
   |---|---|
   | Must things follow in an **order** that results from dependencies? | `graph-order.md` |
   | Do we **pair up** elements of two sets (people with tasks)? | `matching-flow.md` |
   | Do we choose a **subset fitting within limits** (budget, capacity, time)? | `optimization.md` |
   | Do all requirements have to be **covered** with the smallest possible set? | `optimization.md` |
   | Is there a **network, a route, connections**, the cheapest path? | `graph-network.md` |
   | Do we **group** things into disjoint sets / clusters? | `graph-network.md` |
   | Must something **not overlap in time**, or are we looking for free intervals? | `data-structures.md`, `optimization.md` |
   | Are we looking for **similar / almost identical** things? | `search.md` |
   | Do we keep choosing the **next most important** element? | `data-structures.md` |
   Then check the *matching question* of each entry from the indicated family.

A hit in one track is enough for an entry to be a candidate. Do not require agreement of both tracks — it loses real hits.
Each entry has a field **"it is not this if… → see X"**: this is not a rejection, only a pointer to a variant (a separate candidate).

## Confidence
- **high** — both tracks hit, each with a different quote, and the mapping covers ≥ 3 elements of the pattern (e.g. node, edge, weight).
- **medium** — one track and a credible mapping.
- **low** — a speculative mapping. Low confidence is an honest result, not a reason to skip it.


## Hard rules
- Every candidate has ≥ 1 **verbatim quote** with a source and a location (the evidence bank from ddd-discovery-intake or the requirements);
  verify the quote in the source (`grep -F`). Not found → the candidate is dropped; text from a conversation without a source → `unverified`.
- **The domain → algorithm mapping** is complete: what is the node, the edge, the weight, the capacity, the constraint.
- Words signalling a problem for which the catalogue has nothing (forecasting, "what if" simulation, negotiations…) list as
  **"honest gaps"** — these are candidates for a novel core.
- Do not declare "NP-hard" on weak evidence; do not solve the problem in the report.

## Observations across areas
- **Consolidation** — the same algorithm (≥ medium confidence) in ≥ 2 areas → a candidate for merging or a shared kernel.
- **Shared kernel** — the same implementation of the algorithm, different domain models (the boundaries remain).
- **Seam** — the same words, different algorithms → a hint that these are different contexts (ddd-strategic-analysis).

## Archetype + algorithm
When the scan and an archetype (ddd-archetypes) point to the same thing: **the archetype gives the model, the algorithm — the engine**. Enclose the algorithm in a pure
function or a solver behind the archetype's interface (e.g. Availability → an interval tree / an exclusion constraint in the database;
General assignment → a multidimensional knapsack).

## Result: `docs/project/02-domain/algorithms.md`
Format and example: `references/report-format.md`. Write area by area (a long run will not cut off the result).
Cost: read only the family files indicated by the structural track (1–2 files per area), and delegate a scan of many areas
to a subagent that returns only the report.

## Checklist
- [ ] problem class confirmed before the scan
- [ ] both tracks reviewed for each area; candidates with quotes and a complete mapping
- [ ] variants ("it is not this if") and honest gaps listed
- [ ] observations across areas; handoff to ddd-strategic-analysis and arch-tech-selection
