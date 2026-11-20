# Option constraints — configurators where choices depend on each other

## When it applies
- Signal: choosing one option changes which other options are allowed or required.
- Not this: independent options — they are plain features of a product definition.

## Core shape
- **Configuration definition** (owned by product or marketing, versioned): options, option groups, defaults, rules.
- **Rule kinds** to support, each with a business-readable name:
  - *requires* — A → B;
  - *excludes* — not (A and B);
  - *exactly one of* a group;
  - *at least one of* a group;
  - *always required*;
  - *A implies some member of set S*;
  - *A forbids every member of set S*.
- **Configuration session** (owned by the buyer, own id): select, undo, list remaining allowed choices, list what is
  still missing for a valid result.
- **Saved configuration**: the selections plus the definition version they were valid under.

## Rules
- Preselected defaults must satisfy the rules.
- Pairwise checks are not enough: every partial pick can be legal while no complete valid configuration exists (a dead
  end). After each choice, run a **satisfiability check over possible completions** — a SAT solver for boolean rules, a
  constraint solver (CSP/MIP) for numeric rules (sums of load, power budgets). The solver sits behind the model's
  interface (ddd-algorithm-recognition for picking it).
- **Explain** a blocked option: which rules and which earlier choices block it, ideally a minimal conflicting set
  ("Tabletop 200 cm is blocked by *Frame F1 supports ≤ 180 cm* because you chose Frame F1").
- On a choice that contradicts earlier ones: reject, or propose automatic changes (deselect X, select Y). Decide also
  whether required options are added automatically; this may differ by channel (self-service vs sales rep).
- Test the definition itself: every option is reachable in some valid configuration, and no default breaks a rule.
- The UI asks the engine for allowed options; it never copies the rules.

## Decisions to settle
- Conflict handling: reject or auto-repair? Auto-add required options?
- What happens to open sessions and saved configurations when rules change (revalidate, keep on old version, notify)?
- Numeric rules present (sums, limits) → constraint solver needed, or booleans only?
- Who maintains the rules, and how is a new rule set tested before release?

## Belongs elsewhere
- Option prices → price calculation.
- Stock of components → product definitions / value ledger.
- Which buyer may see which options → a policy passed in as input.

## Traps
- `if` chains in the front end toggling checkboxes; the same rules re-coded on the server — and they drift.
- Validating only pairs, then the factory receives unbuildable orders.
- Defaults that already violate a rule.
- A saved configuration without the definition version — nobody knows which rules it passed.

## Worked example
Requirement: an online configurator for modular office desks. Leg frame F1 does not support the 200 cm tabletop; a
monitor arm needs the reinforced top; exactly one cable tray; the factory keeps receiving unbuildable orders.
- Rules: `R1 frame-F1-excludes-top-200`, `R2 monitor-arm-requires-reinforced-top`, `R3 exactly-one-cable-tray`,
  `R4 reinforced-top-only-in {top-200}` (*reinforced implies some member of set*).
- Dead end: the buyer picks frame F1 (legal), then a monitor arm (legal — no rule links F1 and the arm). Pairwise checks
  pass, yet no complete desk exists: the arm needs a reinforced top (R2), which only comes as 200 cm (R4), which F1
  cannot carry (R1). This is how unbuildable orders reached the factory. The satisfiability check after each choice
  blocks the arm once F1 is chosen and explains why: R1 + R2 + R4, given your choice *F1*.
- Default: tray T-basic preselected (satisfies R3).
- Conflict: the buyer insists on the arm after F1 → offer "switch to frame F2?" (auto-repair, decision U for web; reject for
  the sales-rep channel).
- Saved configuration `CFG-7731` stores definition `desk-rules v12`.
