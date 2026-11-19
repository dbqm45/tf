# The Agreement archetype — mapper (agreements, terms, amendments, orders)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements about **mutual obligations of parties** (an agreement, terms, an amendment, an order, a quote) into a model with the agreement
as an entity with an identity, terms in force over time and orders placed on its basis. The effect: you can
answer the question "what was in force on day X and what did we know about it on day Y", and an amendment is a new version of the terms,
not an overwrite of fields. The common protocol (questions, "It depends", the R/A/X check, recording): `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *do the parties take on mutual obligations on terms that are in force for a defined time
and may change?* Yes → it fits. A one-off cart with no terms and no change history → an order is enough
(see below), without a full agreement.

| Signal in the requirements | Fits? |
|---|---|
| "a service agreement", "an amendment changes the price from the 1st day of the month" | ✅ |
| "the terms are in force from–to", "what rate was in force in March?" | ✅ |
| "orders under a framework agreement", "an order with items and a status" | ✅ |
| "a quote valid for 14 days, after acceptance it becomes an agreement" | ✅ (quote → agreement) |
| "how to compute the price from the price list and the discount" | ❌ → Pricing |
| "settling payments, balances, invoices" | ❌ → Accounting |
| "a scan of the agreement, a signature, a file version" | ❌ → Document (`document.md`) |
| "who the party is, what roles it has" | ❌ → Party |
| "booking a room for a date" | ⚠️ borderline |
| "a contract on a financial instrument" | ⚠️ borderline |

**Borderline cases:**
- *A booking as an agreement?* — only "is the slot free" matters → Availability. When the booking has terms (a penalty,
  a price list, changes over time), the agreement describes the obligation, and Availability blocks the resource.
- *Financial instruments* — a Contract in finance (Fowler, the chapters "Trading" and "Derivative Contracts") is a separate,
  specialist family; this file does not settle it, confirm with an expert.

## Model (the essence)
A chain of concepts (the section names of Silverston's ch. 4): **requirement → request → quote
→ agreement → orders on the basis of the agreement (agreement to orders)**. Not every stage is needed;
start with the ones the requirements mention.

- **Agreement** — an identity, **parties in roles** (Party: e.g. the principal, the contractor; roles from Party, not flags),
  a kind, a status, the form of the legal act, the period of validity of the whole.
- **Agreement items** — what is the subject (a product, a service, a scope); a reference to Product, not a copy.
- **Terms (agreement terms)** — a term type + a value + **a period of validity**. A term is data, not code:
  a payment deadline, a penalty, a service response time.
- **Pricing arrangements (agreement pricing)** — the agreement **points to** a price list, a rate or parameters; Pricing computes them.
- **Order** — one obligation: items, parties, adjustments, a status and terms. It may point to
  an agreement; then it takes its terms **as of the order date** (a copy or a reference to the version — a decision).
- **Framework agreement vs order** — our own conclusion: a framework agreement sets common terms and does not give rise to execution
  by itself; each order is a separate obligation with its own status and life cycle.

### Time: the period of validity and amendments
- A term has **a range of validity dates** (from–to). This is the Effectivity / Temporal Property pattern (Fowler, eaaDev): a value
  that depends on the date.
- **An amendment = a new version of a term with an effective date**, not an edit. The old version stays; it ends on the day before the effective date.
- **Reconstructing the state as of a day**: the query "the terms of agreement U on day D" returns the versions whose range covers D.
- **A second date range** (bitemporality): besides "when it is in force" we record "**when it was recorded**". A backdated amendment
  then does not destroy the system's earlier knowledge, and a dispute is settled by two questions: *what was in force on day D*
  and *what did the system know on day W*.

### Status and rules
- **Status** — a cross-cutting pattern (Silverston Vol. 3: the Status chapter): an agreement and an order have a status type, a value
  and an assignment date; the allowed transitions are a rule, not structure.
- **Business rules** (Silverston Vol. 3: Business Rules; Arlow & Neustadt have the Rule archetype) — "an amendment requires
  the acceptance of both parties" is computed by the policy layer, which calls the archetype.
- **The form of the legal act** — an attribute of the agreement (written, documentary, electronic). The legal context to be confirmed by
  a lawyer: the documentary form (art. 77² KC, the Polish Civil Code, from 8.09.2016), the electronic form with a qualified signature
  (art. 78¹ KC). The archetype records the chosen form; **whether the act is valid** is assessed by a lawyer, not by the model.

## Questions
**A — standard decisions:**
- Is there a **framework agreement**, or only individual orders? Must an order point to an agreement?
- Can an amendment act **retroactively**, and is a **second date range** (when it was recorded) needed?
- Does an order **copy** the terms at the moment it is placed, or point to a version of the agreement?
- What **statuses** and transitions do the agreement, the amendment and the order have? Who approves (outside the archetype)?

**B — gaps** (examples): termination · automatic renewal · several amendments with the same effective date · a multi-party
agreement · limits on order values in a framework agreement · assignment (cession).

## Mapping steps
1. **The obligation** — a lasting agreement or a one-off order; is there a framework agreement.
2. **Parties and roles** — who, in what role (a reference to Party; roles as data).
3. **Items and terms** — what is the subject; which terms as type + value + period.
4. **Price** — arrangements in the agreement; Pricing computes.
5. **Time** — the period of validity, amendments as versions, the effective date, a possible second date range.
6. **Orders** — the link to the agreement, inheriting terms.
7. **Status** — states and transitions as rules; change events.
8. **Integrations** — Pricing, Accounting (financial effects), Availability, Product, Document.

## Decisions to check (R/A/X)
framework agreement vs orders · a backdated amendment · the second date range · a copy vs a reference to a version of the terms · statuses
and transitions · the quote stage · who approves an amendment · termination · the form of the legal act.

## Result format
```markdown
# Agreement model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Agreements         — | Kind | Parties and roles (→ Party) | Items | Form of the legal act | Period | Framework? |
## Terms over time    — | Term type | Value/parameter | In force from–to | Recorded from–to (optional) |
## Amendments         — | Amendment | What it changes | Effective date | Backdated? | Approves (outside the archetype) |
## Orders and statuses — | Order | Agreement | Terms: copy/reference | Status | Transition |
## Integrations        — | Event | From / to archetype | Reaction |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), edge cases, variable policy parameters
```

## Patterns and pitfalls
- **Overwriting a term with an amendment** — the history is lost; the dispute "what was the rate in March" cannot be settled. A version with an effective
  date instead of `UPDATE`.
- **One date** ("valid to") with backdated amendments — without a second date range you will not distinguish "was in force" from
  "what we knew then". Add it only when the requirements allow backdated corrections or disputes about the state.
- **Price as logic in the agreement** — the agreement points to a price list and parameters; Pricing computes.
- **The agreement as a file** — the scan and the signature are Document; the agreement has terms and a status independently of the file.
- **An order inheriting terms "live"** — a later amendment will change an old order; decide: a copy or
  the version as of the order date.
- **Authorization outside the archetype**: "who approves an amendment" is computed by the policy layer; the archetype guards the structure (periods
  of one term type without overlap).
- **A quote is not an order:** a quote is one party's proposal with a validity deadline, versions and negotiation;
  it does not reserve resources and binds no one to accept. An order is an obligation with fulfilment, payment
  and complaints. "An order with the status quote" mixes two life cycles and two sets of rules. Accepting a quote is
  a pivotal event that **creates** an order or an agreement with the terms copied from the accepted version.
- **A purchase is not an order:** an order expresses what the customer wants; a purchase (a sales transaction) is the fact of settlement,
  i.e. payment, an invoice and the transfer of ownership (Accounting). One order is sometimes fulfilled by several purchases
  or deliveries, and a purchase in a brick-and-mortar shop has no order. A shared `orders` table with a `paid` status hides these
  differences.

## Quality check
- [ ] the parties appear in roles from Party, without flags
- [ ] every term has a type, a value and a period of validity; periods of the same type do not overlap
- [ ] an amendment is a new version with an effective date; the state as of a day can be reconstructed
- [ ] the decision about the second date range (when it was recorded) taken explicitly
- [ ] the boundaries indicated (Pricing, Accounting, Document, Availability); the form of the legal act only as an attribute
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A service company: a service agreement with a customer for 24 months, an hourly rate and a response time. Amendments
change the rate and the scope from an indicated date, sometimes retroactively. The customer orders visits under the agreement. The customer claims that
in March the rate was 100, we have 120." [example]

```markdown
## Concept mapping
| service agreement | Agreement (framework) | the terms last longer than one visit |
| rate, response time | Agreement terms (type + value + period) | they change with amendments |
| ordered visit | Order on the basis of the agreement | a separate obligation with a status |
## Amendments — | A1 | rate 100 → 120 | from 1 April | backdated: no | approves: policy (outside the archetype) |
## Terms over time — | rate | 100 | 1 January–31 March | recorded: from signing |
                      | rate | 120 | from 1 April | recorded: from A1 |
## Dispute about the state — as of 15 March → 100; with a backdated amendment the second date range will show what the system knew
## Decisions — framework agreement (R) · amendment as a version (R) · second date range (A: "It depends" — only for backdated amendments)
   · order: a copy of the terms at the moment it is placed (X → ask)
## Unmapped concepts — computing the amount for a visit (→ Pricing) · invoice and payment (→ Accounting) · scan with a signature
   (→ Document) · customer (→ Party)
```

## Sources
Accessed 2026-10-17.
- **Silverston, "The Data Model Resource Book, Vol. 1, Revised Edition", Wiley, ISBN 978-0-471-38023-8** (March 2001,
  replaces the 1997 edition) — the section names of ch. 4 "Ordering Products" (confirmed secondarily, by the O'Reilly table
  of contents); the content of the chapters was not verified.
- **Silverston & Agnew, "The Data Model Resource Book, Vol. 3: Universal Patterns for Data Modeling", Wiley 2009,
  ISBN 978-0-470-17845-4** — the chapter titles Status and Business Rules (numbering uncertain); primary.
- **Fowler, "Analysis Patterns: Reusable Object Models", Addison-Wesley** (year 1996/1997) — the titles of ch. 9 "Trading"
  and 10 "Derivative Contracts"; only to mark the boundary (financial instruments).
- **Fowler, martinfowler.com/eaaDev: Temporal Property, Effectivity, Audit Log** — drafts from 2004, the author does not
  update them (primary, not updated). The pattern names; the description of the second date range is our modelling conclusion.
- **Arlow & Neustadt, "Enterprise Patterns and MDA", Addison-Wesley, ISBN 0-321-11230-X** (year: the sources contradict each other,
  2003/2004) — only the names of the Order and Rule archetypes; the content was not verified (secondary).
- **Kodeks cywilny (the Polish Civil Code), art. 77² (documentary form, from 8.09.2016; the act of 10.07.2015, Dz.U. 2015 item 1311), art. 77³
  (document), art. 78¹ (electronic form)** — the legal context from a commentary (secondary); to be confirmed by a lawyer.
- Quote vs order and purchase vs order — based on the programme of the training "DDD — zaawansowane techniki
  modelowania i archetypy" (DDD — advanced modelling techniques and archetypes; Bottega IT Minds, material from a human, 2026-10-21); described in our own words.

The rest (framework agreement vs order, a copy vs a reference to a version of the terms, the second date range, rules and pitfalls) are
our modelling conclusions, not attributed to the authors. Described in our own words; the content of books and standards was not quoted.
