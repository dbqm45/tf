# Analysis of a single flow (deepening after the map)

The repo map says where to look. Flow analysis says **how one flow works today** (e.g. "saving a message",
"calculating a discount") and what is fragile in it — before a decision about a change. The result is input to a step's plan or to
choosing a refactoring (eng-refactor-planning). An audit of a whole module in many dimensions is eng-tech-debt-audit;
the cause of a specific bug — eng-debugging.

## 1. Scope contract
- **Input:** the repo map as a prior — the target from "Risk zones", 2–3 starting files from "First day", the first
  `unknowns` from "Limitations". Without a map: the map first, or the human's explicit consent to an analysis without it.
- **One flow**, not a subsystem. At the top of the report one line with the goal: what I am researching, from which file, why the map
  pointed to this area.
- **Hard boundary:** only the current state — no refactoring proposals and no target architecture.

## 2. Three implementers in parallel (the same contract, read only)
1. **Trace end-to-end:** from the entry point through the layers to the write or read and back; steps with `file:line`;
   a sequence diagram (Mermaid). Where the data comes from, who validates, where the state changes, what returns. Both sides (e.g.
   an optimistic UI and the server) and the place where they reconcile. Name the layers that only delegate explicitly.
2. **Test gaps:** which methods and branches of the path have a test (the test name), which do not — especially the error paths.
3. **Change reach:** what must change together — the interface seam, generated layers, the model, migrations, tests;
   the static graph + co-changes from `git_territory.py --cochange` (pair vs hub).
Every claim with an evidence / inference / unknown label.

## 3. The report `docs/project/<step>/research.md`
1. **Goal** (1 line).
2. **Flow overview** — the flow, not a list of files; a sequence diagram.
3. **Debt as a fragility map:** the kind of risk in the language of connascence (order, meaning, position, algorithm;
   static vs dynamic; distance), gaps in the test net, reach. **Cheap couplings separately** — generated code,
   regeneration, things caught by the compiler or CI. Do not write "tightly coupled"; name the kind.
4. **Prior corrections:** what from the map turned out to be outdated — explicitly, with evidence.
5. **Unknowns** with how to resolve them (whom to ask, what to run).
6. **Verification of structural claims** ("exactly 4 calls", "only here", "always through X"): each one
   checked with ast-grep or LSP, every zero confirmed with `rg`; corrections in place with the trace "5 (report: 4)";
   a table claim → verdict → evidence → method.
7. **Flow hotspots:** change frequency from the map × the complexity of the flow's files (a cheap proxy, e.g. non-empty lines).

## 4. Report review criteria (a human, fresh context)
- a flow instead of a list of files?
- debt named by the kind of risk, and the cheap kind separated from the dangerous one?
- numbers verified with a tool, zeros confirmed?
- nothing proposes changes?

## 5. Example
The "saving a message" flow: 6 layers in directories, of which 4 only delegate; a single save is a facade over a
batch save; saved objects are not read back from the database. Fragility: a positional write of 18 columns (connascence
of position, without a guard); the message model on the backend and its hand-made copy on the front end (meaning, large distance, almost
zero co-changes — silent debt); error paths without tests. Cheap: store layers generated from the interface (a mismatch
is caught by CI). Prior correction: the map gave 3 delegating layers, there are 4. Verification: "4 batch save calls"
→ 5 (report: 4), the fifth in an integration test.
