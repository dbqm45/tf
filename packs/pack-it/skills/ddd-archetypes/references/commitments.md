# Commitments — contracts, terms, amendments, quotes and orders

## When it applies
- Signal: parties commit to each other under terms that hold for a period and can change (service contracts, insurance
  policies, leases, framework agreements, employment).
- Not this: a single purchase without lasting terms — an order alone is enough.

## Core shape
- Full chain (use only what the requirements need): need → request for quote → **quote** → **contract** → **orders**
  placed under the contract.
- **Contract**: identity, parties in roles (references to the party model), kind, status, legal form, overall validity.
  Its items reference products or services; they do not copy them.
- **Term**: type + value + validity range — payment deadline 30 days, penalty 0.5% per day, response time 4 h. Data,
  not code. Periods of the same term type on one contract never overlap.
- **Amendment**: adds a new term version starting on a given day; the previous version ends the day before. Nothing is
  updated in place. An *as-of D* query selects the term versions whose window contains D.
- **Bitemporal option**: also record when each fact was entered (recorded time) next to when it applies (valid time).
  That separates "what applied on D" from "what we knew on W" — needed for backdated amendments and disputes. Add it only
  when retroactive changes or disputes are in scope.
- **Status**: type + value + date assigned. Allowed transitions are rules enforced by the policy layer (e.g. an amendment
  becomes effective only after both parties accept).
- **Quote**: a proposal from one side, versioned, with an expiry. It reserves nothing and obliges nobody. **Accepting it
  is the event** that creates the order or contract, copying the terms of the accepted version.
- **Order** (intent) ≠ **sale/purchase** (settlement: payment, invoice, transfer of ownership). One order may be settled
  by several deliveries or payments; a cash-counter sale has no order.

- **Portfolio**: a group of contracts or orders defined by a **filter** (by counterparty, product, region, end date)
  with aggregate behaviour — total exposure, value under a rate set, renewals due. A contract belongs to many
  portfolios; membership follows from the filter, never from manual tagging. Computing it on demand or keeping it
  maintained is an implementation choice hidden from its users.

## Rules
- Price arrangements point to price lists or parameters; computation stays in price calculation.
- A framework contract fixes common terms and triggers no delivery by itself; each order is a distinct obligation with its
  own lifecycle. Decide: the order **copies** the terms at placement, or **references** the term version valid on the
  order date. Inheriting terms "live" lets later amendments change old orders.
- The legal form (written, documentary, electronic with a qualified signature) is only recorded; whether it is legally
  valid is a question for a lawyer.
- Contracts on financial instruments (derivatives, securities) are a specialist area outside this skill — point to an
  expert.

## Decisions to settle
- Termination rules and notice periods; auto-renewal.
- Several amendments effective on the same day — order of application?
- Multi-party contracts.
- Order value caps under a framework.
- Assignment of the contract to a third party.
- Copy vs reference of terms on orders.

## Belongs elsewhere
- Premiums, fees, penalties → price calculation; their posting → value ledger.
- Signed files and what was sent → evidence documents.
- Parties and their relationships → parties and relationships.

## Traps
- A quote modelled as an order with `status = 'quote'` — different lifecycles, a quote reserves nothing and can expire,
  an order obliges.
- `UPDATE contract SET price = …` on an amendment — the dispute about last March cannot be settled.
- Orders reading the framework's current terms, so an amendment silently changes past orders.
- One `valid_from` per contract while each term changes on its own dates.

## Worked example
Requirement: insurance policies get endorsements that change the premium or coverage from a date, sometimes backdated;
claims handlers need the cover on the loss date; auditors ask what we believed at the time; brokers send quotes before
binding.
- Quote `Q-5510 v2` (broker party in role *intermediary*, expires 2026-06-30); binding = accepting v2 → policy `P-7781`
  created with v2's terms copied.
- Terms: `coverage-limit 500k [2026-07-01, ∞)`, `deductible 2k [2026-07-01, ∞)`.
- Endorsement recorded 2026-09-15, valid from 2026-09-01: `coverage-limit 750k [2026-09-01, ∞)`; the old version now
  ends 2026-08-31. Bitemporal: valid time 09-01, recorded time 09-15.
- Claim with loss on 2026-09-05: as-of valid 09-05 → 750k. Auditor's question "what did we believe on 09-10?": as-of
  valid 09-05, recorded ≤ 09-10 → 500k.
- Status *endorsed* allowed only after underwriter approval (policy). Premium recalculation → price calculation; signed
  endorsement PDF → evidence documents.
