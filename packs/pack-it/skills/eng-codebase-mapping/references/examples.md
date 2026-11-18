# Code map examples

## 1. A map of an unfamiliar Nx repository
**Situation:** "I got the `shop` repo (Nx, Angular + NestJS). Where should I start reading and what is the core?"

**How:**
1. **Inventory:** 3 projects, 84 TS files, about 9 thousand lines — below ~100 files in scope, so no scope agreement needed.
2. **Graph from tools:** `nx graph --file=graph.json` for projects, `madge --json apps/api/src` and `madge --circular` for files.
3. **Entry points** by score (name +3, root/one level lower +1, top 10% of outgoing imports +1, bottom 25% of
   incoming +1).
4. **Layers and direction:** controllers → services → repositories; an upstream arrow is a finding.
5. **Central nodes** after filtering out `index.ts` barrels; **cycles** listed; edges with a confidence label.
6. **Write-up:** `docs/project/04-architecture/codebase-map.md`, date and commit `a1b2c3d`.

**Result** (a fragment of the map):

| Entry point candidate | Name | Level | Outgoing | Incoming | Total |
|---|---|---|---|---|---|
| `apps/api/src/main.ts` | +3 | +1 | +1 | +1 | **6** |
| `apps/web/src/app/app.config.ts` | +3 | +1 | +1 | +1 | **6** |
| `apps/web/src/app/app.routes.ts` | +3 | +1 | 0 | 0 | 4 |
| `libs/orders/src/order.service.ts` | 0 | 0 | +1 | 0 | 1 |

Layers (API): `orders/*.controller.ts` → `orders/order.service.ts` → `orders/order.repository.ts` → `libs/db`.
Finding: `libs/db/src/audit.ts` imports `order.service.ts` — an upstream arrow, it creates the cycle
`order.service.ts → order.repository.ts → audit.ts → order.service.ts` (EXTRACTED, madge).
Central node: `order.service.ts` (23 connections) — here a change has the widest reach.
The edge `PaymentsModule → StripeGateway` through a DI token: INFERRED (from the module configuration, not from an import).

Reading route (fragment, 7 steps):
1. `apps/api/src/main.ts` + `app.module.ts` — how the API starts and which modules it loads.
2. `orders/orders.controller.ts` — the endpoints, i.e. what the system does for the client.
3. `order.service.ts` + `order.repository.ts` — the core of the order rules and persistence; the most connections.
4. `libs/db/src/audit.ts` — the cause of the cycle, before you change anything in orders.

## 2. Diff impact for a PR description
**Situation:** "Assess the impact of my branch before review — I changed how the discount is calculated."

**How:**
1. Changed files: `git diff --name-only main...HEAD` → 3 files.
2. Map freshness: `git diff --name-only a1b2c3d HEAD -- libs/pricing` shows only the 3 files of this branch, so the map of
   `libs/pricing` is current; in Nx additionally `nx show projects --affected` → `pricing`, `api`, `web`.
3. For each file 1 step up and 1 down, the affected layers.
4. Risk from complexity, edges between layers and reach.

**Result** (for the PR description):

| File | Who uses it (↑) | What it uses (↓) | Layers | Risk |
|---|---|---|---|---|
| `libs/pricing/src/discount.ts` | `order.service.ts`, `cart.store.ts` | `money.ts` | services, UI | **high** — 2 applications |
| `libs/pricing/src/money.ts` | `discount.ts`, `invoice.ts` | — | utilities | medium — a foundation |
| `libs/pricing/src/discount.spec.ts` | — | `discount.ts` | tests | low |

What to test (qa-regression): the cart in `web`, placing an order and the invoice in `api`.
