# Logic and data access patterns (PoEAA)

The classic patterns from *Patterns of Enterprise Application Architecture* (M. Fowler) — the vocabulary you name decisions with
in ADRs and reviews. Tactical DDD (aggregates, domain repositories): ddd-tactical-design.

## 1. Where the business logic lives
| Pattern | What it is | When | A signal that it is no longer enough |
|---|---|---|---|
| **Transaction Script** | one procedure per request: validates, computes, writes | simple CRUD, few rules, reports, integrations | the same rules copied into many scripts; scripts of several hundred lines with `if`s on types |
| **Table Module** | one class per table, operates on sets of records | rarely today; ecosystems with in-memory records | — |
| **Domain Model** | objects with data and behaviour, invariants inside | many rules that change (the core subdomain) | — (cost: mapping, the ORM, learning) |
The choice depends on the complexity of the logic, not on fashion: a generic subdomain → a transaction script, the core → a domain model
(ddd-strategic-analysis). Going the other way is expensive, so the decision goes into an ADR.
**An anemic model** = domain classes with only fields and "services" with the logic — it is a transaction script with the overhead of a model.
A conscious transaction script is more honest than an anemic model pretending to be a domain model.

## 2. Mapping objects to the database
| Pattern | What it is | Notes |
|---|---|---|
| **Active Record** | an object = a row, it saves itself (`order.save()`) | a quick start, but the domain depends on the database; good for simple models |
| **Data Mapper** | a separate mapper moves data between the object and the database; the object does not know about the database | required for a domain model independent of the infrastructure |
| **Repository** | a collection of aggregates from the domain's perspective (`orders.byId(id)`, `orders.save(order)`) | the interface in the domain, the implementation in the infrastructure; no generic `findAll(filter)` for every case |
| **Unit of Work** | tracks changes to objects within a transaction and writes them together | the boundary = one transaction = usually one aggregate |
| **Identity Map** | within one unit of work one object per identifier | no two copies of the same record, fewer queries; it is not a cache between requests |
| **Lazy Load** | related data loaded on first use | a source of N+1 and of errors after the session is closed — in reads explicit `join`/eager or DTOs |

What popular tools give:
- JPA/Hibernate: the persistence context = Identity Map + Unit of Work (change tracking, writes at `flush`).
- MikroORM: Data Mapper with Unit of Work and Identity Map.
- TypeORM: both styles (Active Record and Data Mapper), without a full Unit of Work.
- Prisma: a query client without Identity Map and Unit of Work; you ensure consistency with a transaction (`$transaction`).
Check the version and the documentation in the project (core-stack-sync) before you design something that assumes these mechanisms.

## 3. Writes through the ORM, reads through SQL
- The write side (state changes, invariants): an ORM with Unit of Work, the aggregate loaded in full.
- The read side (lists, reports, search): an SQL query, a view or a light builder returning a **DTO** fitted
  to the screen — without loading aggregates and without lazy loading. This is a light form of CQRS (ddd-tactical-design), without a separate database.
- An ORM is a leaky abstraction: knowledge of SQL, query plans and indexes is still needed (SKILL.md).

## 4. DTOs and mappers
- A **DTO** carries data across a boundary (an API, a queue, the read layer): simple fields, without behaviour, versioned like
  a contract (be-api-design). Neither an entity nor an aggregate leaves its module.
- A **mapper** translates representations (a row ↔ a domain object, a domain object ↔ a DTO) in a layer that knows both sides —
  usually the application or the infrastructure, never in the domain.
- Mapping written by hand is explicit and typed (TS has no runtime reflection); generators (MapStruct
  in Java) — with many simple DTOs. A mapper test: fields added to a DTO without mapping must cause a compile or
  test error, not a silent `undefined`.

## Sources
- M. Fowler, *Patterns of Enterprise Application Architecture* (2002);
  [the pattern catalogue](https://martinfowler.com/eaaCatalog/) (among others [Transaction Script](https://martinfowler.com/eaaCatalog/transactionScript.html)).
- V. Khorikov, [Do you need an ORM?](https://enterprisecraftsmanship.com/posts/do-you-need-an-orm/) — an ORM on the
  write side, SQL on the read side, Identity Map, Unit of Work, lazy loading pitfalls.
- [roadmap.sh — Software Design and Architecture](https://roadmap.sh/software-design-architecture) (enterprise patterns).
Described in our own words.
