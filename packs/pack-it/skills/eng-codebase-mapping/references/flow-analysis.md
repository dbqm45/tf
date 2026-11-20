# Deepening one flow — current-state analysis


## 1. Input and boundaries
- **Input:** the codebase map as a prior — the risk zone this flow belongs to, 2–3 starting files, the first unknowns. No map → ask for
  one first (the procedure in SKILL.md) or for the human's explicit consent to start without it, and say in the report that there was none.
- **One flow** (e.g. "redeeming a coupon at checkout"), named in one goal line.
- **Current state only.** No proposals, no target architecture, no refactoring plan — those belong to eng-refactor-planning, which uses
  this report as input. The cause of one specific bug: eng-debugging.

## 2. Three read-only investigations
Split the work among parallel workers that only read. Each labels every statement **evidence** (file:line seen), **inference**
(reasoned from evidence) or **unknown**.

| Worker | Delivers |
|---|---|
| **trace** | the end-to-end path with `file:line` per hop; a Mermaid sequence diagram showing both sides of every call and the point where results are reconciled; layers that only delegate are named as such |
| **test gaps** | which hops have tests and at what level; untested branches, especially error and timeout paths |
| **change reach** | seams where the flow could be cut; generated layers (clients, ORM models); the data model and migrations; tests that would need to change; co-changes from history — a pair vs a hub |

## 3. The report
Sections, in this order:
1. **Goal** — one line: which flow, from which entry point to which effect.
2. **Flow overview** — the sequence diagram and a hop table (layer · file:line · what it does · label).
3. **Fragility map** — debt described as couplings in connascence terms: order (positional arguments or columns), meaning (magic values
   shared by two sides), position, algorithm (the same calculation in two places); static vs dynamic; the distance between the coupled parts
   (same function → different services). Cheap couplings (generated, checked by a compiler) are listed separately so they do not inflate the map.
4. **Corrections to the prior** — where the map was wrong or incomplete, with evidence.
5. **Unknowns** — runtime wiring, configuration, external systems not read.
6. **Verifying structural claims** — every count or "called in N places" checked with `ast-grep` or LSP find-references; every zero
   confirmed with `rg`; corrections written in place as `5 (report: 4)`.
7. **Flow hotspots** — files of the flow ranked by change frequency × size (`git_territory.py --hotspots`).

## 4. Reviewing the report
A human with fresh context reads it and checks:
- every hop has `file:line` and a label; no proposal or target design slipped in;
- the sequence diagram matches the hop table;
- error paths appear in the test-gap section;
- counts were verified and zeros confirmed;
- the unknowns are specific enough to check ("the `coupon.redeemed` consumer in another repo"), not "maybe something else".

## 5. Example — coupon redemption
Goal: `POST /checkout/coupons` → coupon marked used and discount applied to the cart.

Hop table (excerpt):
| Layer | Location | What it does | Label |
|---|---|---|---|
| API | `api/checkout.py:41` | parses body, calls the service | evidence |
| service | `checkout/coupons.py:88` | validates, calls `pricing.apply_discount` | evidence |
| pricing | `pricing/discount.py:17` | computes the discount; the same rounding as `web/src/cart/total.ts:52` | evidence |
| repository | `checkout/repo.py:130` | `UPDATE coupons SET used_at` and inserts a redemption row | evidence |
| event | `checkout/coupons.py:112` | publishes `coupon.redeemed`; consumer outside this repo | unknown |

Fragility map: connascence of algorithm between `pricing/discount.py:17` and `web/src/cart/total.ts:52` (dynamic risk — totals can disagree
by 0.01; far apart: backend vs frontend); connascence of meaning on the status string `"USED"` in three files; the generated TS client
↔ OpenAPI schema is a cheap coupling. Test gaps: no test for "coupon expired between validation and update". Correction to the prior:
the map called `checkout/repo.py` a thin adapter; it holds the uniqueness rule (`repo.py:126`). Verification: "`apply_discount` is called
in 2 places" → `3 (report: 2)`, the third in `admin/refunds.py:64`.
