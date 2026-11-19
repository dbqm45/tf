---
name: ddd-connascence-analysis
description: Use for measuring the coupling of two modules or contexts — evidence in the code, the connascence degree, cost.
metadata:
  review: "2027-10-17"
  catalog: "Use when MEASURING the coupling between two modules/contexts (existing code or a context map) — breaking it into single contracts, a repeatable evidence search, the degree counted from lines of code, cost, a band profile, a decision register. Not for designing the model inside a context (ddd-tactical-design) or choosing a relationship pattern (ddd-context-mapping)."
---

# Measuring connascence on the boundary of two modules

The vocabulary of kinds and strength is in ddd-tactical-design. This skill turns an assessment "by eye" into a **repeatable measurement**:
two runs on the same code are to give the same set of the most dangerous couplings.

## Rules
1. **Always one pair** A ↔ B. Only what **crosses the boundary** counts — that is locality, recorded in the scope.
2. **One row = one contract of one kind.** One fact in the code can give several rows (rules: `references/taxonomy.md`).
3. **The degree is counted, not estimated:** degree = the number of places in production code that must change when the contract changes
   (an import and an unused declaration do not count; tests are counted separately). Details: `references/scoring.md`.
4. **Every claim has a source** (`code:path:line`, `search:<pattern>`, `doc:path§section`, `human:Q3`).
   A claim without a source is an `assumption:` — listed, but without a cost and outside the totals.
5. **Compare the set of culprits and the band shares, never the totals** (the cost is ordinal, not "points").

## Procedure (a gate after steps 0, 1, 2 — the protocol is in ddd-facilitation)
0. **Frame:** what belongs to A and to B (paths, packages), the local rules of the stack: where the tests are, what an import looks like, the transaction marker,
   write operations, shared instances (singleton, DI). Recorded in `docs/project/02-domain/connascence/<a>-<b>.frame.md`
   — the next run starts from the same frame.
1. **Collecting evidence — the `scout` subagent following the recipe** (`references/evidence.md`): the public surface of both sides, a search
   for each symbol on the other side in both directions, a separate search for dynamic couplings (transactions, shared stores,
   shared instances, time and retries). It returns a list of `file:line` hits + the searches performed — **without assessments**.
   Starting point (Python, TS/JS): `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo> --focus <A>
   --focus <B>` — the files crossing the boundary in both directions; an import alone does not count towards the degree, it is a list of places to
   check, and the graph does not see dynamic couplings.
   Gate: the human cuts off false hits before the most expensive step.
2. **Classification and cost** (the main thread — it sees the whole seam): rows by kind, degree, cost, bands.
3. **Report** `docs/project/02-domain/connascence/<a>-<b>.md`:
   - tables per kind (each of the 9 kinds has rows **or** a described absence with evidence that it was searched for),
   - a cost table sorted deterministically (cost ↓, then path, line),
   - **band profile:** static weak (name, type) · static semantic (meaning, position, algorithm) · dynamic
     (execution order, timing, value, identity) — the number of rows, the total, the share,
   - the largest couplings with a recommendation for weakening them (the refactoring table in ddd-tactical-design),
   - unused public surface (candidates for hiding),
   - **decision register** — every case the rules did not settle, and how it was counted.

## Without code
On a context map or contracts it works the same way, but the degrees are **ranges** (`2–4`), and missing evidence is explicit.
When the map and the code differ — give both sources; the code decides.

## Interpretation
- An Open Host / Published Language relationship should give mainly the static weak band.
- Dynamic rows across the boundary (a shared transaction, two stores that must agree) = the boundary leaks →
  one data owner + events / a saga (ddd-context-mapping, be-messaging-outbox).
- Fitness function: the dynamic band on critical boundaries does not grow between releases (arch-quality-attributes).

## Cost
The search (the most expensive part) is done by `scout` on a cheap model; the main thread gets only the rows. Analyse the pairs indicated by the context
map or a reported problem — not all pairs. Assess a small, obvious seam right away, without a subagent.
