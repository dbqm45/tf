# Assessing the impact of requirements on modules

1. **An inventory of modules**, and when the sources allow — **an inventory of capabilities** (public operations / facades) of each module.
2. For each requirement and module — **a check of the structure**:
   - **uses** — uses an existing operation without a change (does not count as a change, but goes into the justification),
   - **extends** — changes an existing operation,
   - **gains** — gets a new operation,
   - **no place** — no module is a natural place → a new module is needed.
3. The requirement's class: **local** (0–1 changed modules; "composition only" = existing operations exclusively) ·
   **distributed** (≥ 2) · **new module** (wins; notation `N (+1 new)`). A range → classify by the upper bound.
4. Every row has a **"why"** — why the change touches exactly these modules, no fewer and no more. Purely
   technical components (logging, auth) you skip.

## Report (`docs/project/02-domain/stress/<metric>.md`)
the metric · the frozen set of requirements (with the source marker) · a table requirement → modules (uses/extends/gains/no place) →
class → why · a summary per module (the change column separately from the use column) · the distribution of classes · a note: "this set can be
repeated on another decomposition". No quality judgements; conclusions and decisions — the human, an ADR.
