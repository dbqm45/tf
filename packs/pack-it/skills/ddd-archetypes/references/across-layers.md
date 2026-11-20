# Across layers — modules, communication, UI rules, code smells, refusals

## Where an archetype shows up in each layer
| Layer | What lives there |
|---|---|
| Domain | the rules and invariants of the archetype; algorithms behind its interface |
| Module edge | a small contract; translation between transfer objects and domain objects |
| Integration | events between modules; read models built on the receiver side |
| Read side | consolidated views — calendars from merged hold slices, entry histories, catalogs |
| UI | reflects state and gives hints; decides nothing |

Apply the archetype in a layer when the concept recurs and must stay consistent, mistakes are costly, or the other side
already exposes that shape. Skip it for a single trivial CRUD screen or a one-off script.

## Module communication
- **Synchronous facade** when the caller needs an immediate yes/no (did the hold succeed?). A transaction spanning two
  modules is a deliberate, documented compromise — the next step is a saga or an outbox.
- **Events**: private events inside a module; published-language events at its edge (a stable schema for others).
- **Anti-corruption layer**: a pure translation function for legacy or external data (geocoders, ERP, supplier feeds).
- **Saga / process manager** for reactions across modules (release → offer → hold → accept), with explicit stored state.
- Enforce import boundaries with an architecture test or a lint rule; no dependency cycles; shared types (money,
  quantity, ids) in a small shared kernel.
- Responsibility levels: capability → operations → policies → decision support; each depends only on the levels below
  (the "responsibility layers" idea in Evans, *Domain-Driven Design*, 2003).

## UI rules
- The server computes every payable amount; a local preview is labelled approximate and never submitted.
- Contested resources are never booked optimistically: show a pending state; a conflict is an expected result, not an
  error page.
- No floats for money; one formatter for the whole UI.
- Rules (allowed options, required fields, address templates) arrive as data from the engine.
- The UI speaks business words ("Your spot is held until 14:20"), not archetype names.

## Code smells and remedies
| Smell | Archetype | Remedy |
|---|---|---|
| `float`/`double` money, a separate `currency` string, rounding in many places | quantity and money | money value object with ISO 4217 currency; one rounding policy |
| value and unit as two strings | quantity and money | quantity value object with unit and dimension |
| `isCompany`, `isCustomer`, `isSupplier` flags; separate `User`, `Customer`, `Lead` classes for one real party | parties | one party with roles and relationships |
| `reserved` / `maintenance` flags plus hand-written overlap checks | resource holds | one hold model; reasons are clients; database guard |
| hard-coded feature columns; one form per product type | product definitions | feature definitions as data |
| `if` chains toggling options | option constraints | declarative rules + satisfiability check |
| discounts or interest computed in a service or a view | price calculation | calculator tree with versioned price list |
| a balance column written directly; corrections overwrite | value ledger | transactions, entries, reversals |
| `ORDER BY created_at` as the waiting order | waiting list | priority list with offers and timeouts |
| hand-coded resource-to-task matching | task selection | optimiser behind an interface + domain adapter |

## When to refuse or redirect
- **No business archetype**: a device controller state machine, a protocol parser, a rendering pipeline — say no
  archetype applies and do not force one; point to general design (ddd-tactical-design, eng-design-principles).
- **No requirements given** ("map our loyalty idea onto the ledger"): ask for the domain description once; without a
  human, list the open questions — earning rules, expiry, reversals, transfer — and mark nothing as decided.
- **Neighbour questions**: a context map between billing and shipping → ddd-context-mapping; design pattern choice in code →
  eng-design-principles; subdomain classification → ddd-strategic-analysis; payment-provider subscription mechanics →
  be-billing-subscriptions; ADRs and repository docs → docs-tech-writing.

## Worked example — code review
Input: a review of `CheckoutService` with `double price`, a `Company.isSupplier` flag and `UPDATE members SET points =
points + ?`.
- Money smell: replace `double` with a money type (decimal + currency), rounding once at the document total.
- Party smell: `isSupplier` → role *supplier* on the party; supplier-specific data in the role's context.
- Ledger smell: points as a ledger — an accrual transaction with the order id as unique source event; a reversing
  transaction on return; no direct `UPDATE` of the balance.
- Order of change: money first (smallest, highest risk), then the ledger (needs a migration of balances into opening
  entries), then the party roles (eng-behavior-preserving-refactoring).
