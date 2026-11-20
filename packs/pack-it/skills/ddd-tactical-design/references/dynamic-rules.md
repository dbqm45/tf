# Dynamic rules — configurable, versioned and history-dependent

For rules that are not one fixed `if`: they come in variants, they are built from configuration, they change on a known
date, or they depend on what happened before. Used by ddd-tactical-design (section 10).


## 1. A policy is a pure function
A policy takes the context of one case and returns a result: a discount, a penalty, a limit, a decision. It has no state
and does no I/O, so it is tested with plain values.

The result carries its **reason** — which rule fired, with which inputs. Without it, data-driven rules cannot be explained
to a customer, audited or tested meaningfully.

```ts
type LateFee = { amount: Money; reason: string };
type LateFeePolicy = (c: { daysLate: number; invoiceTotal: Money }) => LateFee;
```

## 2. Composing policies
| Shape | When | Example |
|---|---|---|
| Chain | try handlers in order until one answers | VIP rule → contract rule → default rule |
| Tree | combine simple leaves with nodes: AND, OR, NOT, first match, sum, minimum | "minimum of (contract cap, 10% of total)" |
| Decorator | wrap a policy with a cross-cutting step | cap the result, round it, record the reason, apply a per-customer exception |

A **specification** is the yes/no special case of a tree: conditions named in business language and combined
(`isOverdue.and(not(hasPaymentPlan))`).

## 3. Building policies from configuration
- A **policy factory** builds the tree from configuration held as data — the knowledge level of the model: which blocks,
  which parameters, in which combination.
- Validate the configuration before use: only known block types, correct parameter types, no cycles. Version it like code.
- A dozen or so block types is a healthy range. When the business starts to "program" in configuration — loops,
  variables, calls to other systems — you are building a rules engine or a DSL. That is an architectural decision: write an ADR.

## 4. Scoring
A scoring policy turns features of a case into points and a decision:
- **components** — each maps one feature to points ("account age over 2 years → +15");
- a **combining function** — sum, weighted sum or minimum;
- **thresholds** — points to decision ("≥ 60 → approve, 40–59 → manual review, < 40 → reject");
- a **breakdown** — which component gave how many points.
Version the components and thresholds. Store with each decision the scoring version and the breakdown: it is needed for
audits and for appeals. Weights learned from data rather than set by experts: ai-research-methods, data-analysis.

## 5. Rules that change over time
- Every rule version has a **validity period**.
- A case is settled by the version valid on the **relevant date** for that case — the date of the event, of the contract
  or of the report — not the date the computation runs. Which date is relevant is a domain decision: ask the expert.
- A new version is a **new class or function** (`LateFeeRules2025`, `LateFeeRules2026`) registered with its "valid from"
  date. Do not add year conditions to the old class.
- The old version stays **untouched**, so old cases still reproduce and old tests still pass. The duplication between
  versions is deliberate: each version is a separate fact of the business (a regulation, a price list).
- The version is chosen in **one place** — a registry or factory keyed by the relevant date — and is recorded in the
  result and in the emitted event.

```ts
const lateFeeRules = [
  { validFrom: "2025-01-01", policy: lateFeeRules2025 },
  { validFrom: "2026-01-01", policy: lateFeeRules2026 },
];
function lateFeeFor(relevantDate: string) {
  const v = lateFeeRules.filter(r => r.validFrom <= relevantDate).at(-1);
  if (!v) throw new NoRulesForDate(relevantDate);
  return v.policy;
}
```

- **Retroactive corrections** (a regulation backdated after cases were settled) need two time axes: when a rule applies
  and when the organisation learned about it. Model it as in `.claude/skills/ddd-archetypes/references/commitments.md`
  (bitemporal option for terms and amendments).

## 6. Rules that depend on history
"The third complaint within a year goes to a supervisor", "block the card after two failed payments in a row", "give a
discount to someone who returns after abandoning a cart".
- The state the rule needs is a fold of the event stream: `events.reduce(evolve, initial)`. With a decider the rule sits
  in `decide`, the bookkeeping in `evolve`.
- With event sourcing the stream is the truth. Without it, keep the minimum the rule needs (e.g. dates of recent complaints),
  not the whole history.
- The order of events is part of the rule, so tests are sequences: Given events, When command, Then events or rejection.
- A new rule that must look at existing history needs a data migration or a new projection built from the past events.

## 7. The aggregate as a state machine
When the allowed operations depend on the stage of the lifecycle:
- give the stage an explicit type; every business method checks the transition in one place;
- a successful transition emits an event; a forbidden one is a rejection with a reason;
- two styles: an enum plus a transition table, or separate types per stage (the State pattern) when stages carry
  different data — e.g. only a `PaidOrder` has a payment reference;
- a trap: a "state" with its own data, rules and owner is a different concept, not a state. Separate it
  (`.claude/skills/ddd-deep-modeling/references/untangling.md`).

## Example
**Situation:** late-payment fees change every January; disputes about invoices from earlier years must be settled by the
rules of their year.
**Result:** a `LateFeePolicy` interface; classes `LateFeeRules2025` and `LateFeeRules2026`, the older one frozen; a
registry chooses by the invoice's due date (the relevant date, confirmed with Finance); each `LateFeeCharged` event carries
`rulesVersion: "2026"` and the reason; tests for 2025 invoices keep passing unchanged after the 2026 rules are added.
