---
name: lang-java
description: Use for Java 17/21+ code — conventions, immutability, errors, domain concepts (value object, variants, aggregate).
metadata:
  review: "2027-04-17"
  catalog: "Use when writing and reviewing Java code (17/21+) — language conventions, immutability, error handling and expressing domain concepts (value object, variants, aggregate, operation result, events) with Java idioms. Not for configuring frameworks (Spring, Jakarta — separate fw-*) or domain modeling (ddd-*)."
  keywords: "Java, wynik operacji, wyjątki czy wynik, sealed interface, record, pattern matching, BigDecimal, wynik rezerwacji, sukces albo konflikt terminu, wyjątki czy wynik w Javie, modeluję wynik operacji, Java 21, operation result, exceptions or result, booking result, success or schedule conflict, exceptions or result in Java, modeling an operation result"
---

# Java

## Language rules
1. Target the current LTS (21): `record`, `sealed`, pattern matching in `switch`, local `var` where the type is obvious.
2. Immutability by default: `final` fields, collections copied (`List.copyOf`, `Set.copyOf`) on the way in and out.
3. `null` is not a domain value: validation in the constructor (`Objects.requireNonNull`), a missing value → `Optional`
   in the return type (not in JPA entity fields or parameters).
4. Money and quantities: `BigDecimal` with an explicit scale and `RoundingMode` — never `double`; compare with `compareTo`, not `equals`, when the scale may differ.
5. Exceptions for programming and infrastructure errors; **business rejections** as an operation result (see below).
6. Encapsulation through packages: types and constructors package-private by default; only the module interface (facade) is public.
   Guard module boundaries with architecture tests (e.g. ArchUnit) or JPMS.
7. No setters in the domain model and no bulk generation of them (Lombok `@Data` on domain entities is an anti-pattern).
8. A domain without framework annotations where possible; ORM mapping in an adapter or with minimal annotations.

## Domain concepts in Java
| Concept (glossary) | Java idiom |
|---|---|
| **value object** | a `record` with validation/normalization in the compact constructor; operations return a new record |
| **identifier / entity** | `record PartyId(String value)` instead of a bare `String`/`UUID`; an entity = a class with identity and behaviour |
| **variants** | a `sealed interface` + `record`s; an exhaustive `switch` with patterns (the compiler forces handling of a new variant) |
| **operation result** | a `sealed interface Result<E, T>` with `Success`/`Failure`, or success/rejection events as the method result |
| **aggregate** | a `final class` with private state, business methods instead of setters, `version` for optimistic locking, a list of events handed over by `pullEvents()` |
| **state machine** | the state as a `sealed interface` (e.g. `Free`/`Blocked`/`Disabled`), transitions in a `switch` with `when` guards |
| **event** | a past-tense `record` implementing the module's `sealed interface` of events |
| **policy** | a functional interface/strategy injected by the aggregate factory |
| **specification** | a `Predicate<T>` with `and/or/negate`, or your own interface with a name in the business language |
| **repository / port** | an `interface` in the domain package operating on aggregates; the adapter (JPA/JDBC) in infrastructure |
| **read model** | a separate `record` + a query (SQL/projection) that bypasses the aggregate |
| **module** | a package with a public facade, the rest package-private; architecture tests guard the dependencies |

Tested implementations (Money, Party, Result, TimeSlot, the ResourceAvailability aggregate with a state machine and events,
a repository port): `references/domain-building-blocks.md`.

## Version-dependent
| Version | Changes relevant to this skill |
|---|---|
| 17 (LTS) | `record`, `sealed` (final), pattern matching for `instanceof`, text blocks, `switch` expressions — **without** patterns in `switch`: handle variants with `if (x instanceof A a) … else if …` or a visitor; no `when` guards |
| 21 (LTS) | pattern matching in `switch` and record patterns (final), `when` guards, exhaustive `switch` on `sealed`; virtual threads; `SequencedCollection` (`getFirst()`, `reversed()`) |

A project on a newer JDK (e.g. 25 LTS) → `detect_stack.py` reports `SKILL_OUTDATED`; update the skill per core-stack-sync
(verify the examples with that version's compiler).

## Checklist
- [ ] compiles without warnings (`-Xlint:all`)
- [ ] no `double` for amounts, no public setters in the domain
- [ ] variants as `sealed` and exhaustive `switch`
- [ ] domain tests without the framework container (plain Java)
