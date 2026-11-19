---
name: lang-csharp
description: Use for C# 12–14 (.NET 8–10) code — conventions, nullable, records, async, value object, aggregate.
metadata:
  review: "2027-01-23"
  catalog: "Use when writing and reviewing C# code on .NET 8–10 (C# 12–14) — language conventions, nullable reference types, records and immutability, an operation result instead of exceptions for business rejections, pattern matching and exhaustive switch, async and CancellationToken, differences between versions (primary constructors, collection expressions, params collections, field, extension blocks, ?.=) and expressing domain concepts with C# idioms. Not for ASP.NET Core — endpoints, validation, OpenAPI, integration tests (fw-aspnet-core), API design independent of technology (be-api-design) or domain modelling (ddd-*)."
  keywords: "C#, csharp, .NET, dotnet, net8.0, net10.0, LangVersion, record, record struct, nullable, wynik operacji w C#, wyjątki czy wynik, switch expression, pattern matching, sealed, primary constructor, konstruktor główny, field keyword, extension members, blok extension, async await, CancellationToken, decimal kwota, obiekt wartości w C#, agregat w C#, operation result in C#, exceptions or result, extension block, decimal amount, value object in C#, aggregate in C#"
---

# C#

## Language rules
1. The language version is set by the platform (`TargetFramework`): net8.0 → C# 12, net9.0 → C# 13, net10.0 → C# 14.
   New syntax = raising the platform; a `LangVersion` higher than the default is a risk (some features need
   runtime support) — only deliberately and with tests.
2. `<Nullable>enable</Nullable>` and `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` in every project;
   `null` is not a domain value — you express a missing value with a type (`T?` at the boundary, variants in the domain).
3. Immutability: `record` / `readonly record struct` for values, `init` instead of `set`, collections exposed as
   `IReadOnlyList<T>`.
4. Money: `decimal` with an explicit currency and rounding (`MidpointRounding`) — never `double`/`float`.
5. Exceptions for programmer and infrastructure errors; **business rejections** as an operation result (a closed
   hierarchy of records + `switch`), mapped to a response at the boundary (fw-aspnet-core).
6. Async all the way: I/O methods `async Task`, `CancellationToken` as the last parameter and passed on;
   no `.Result`/`.Wait()` (deadlocks, blocking pool threads).
7. Identifiers as types (`readonly record struct ResourceId(Guid Value)`), not a bare `Guid`/`string`.
8. Module boundaries: `internal` by default, only the project API public; dependencies between projects only
   in one direction (the domain does not know the infrastructure).

## Domain concepts in csharp
<!-- Contract: every concept from the vocabulary → an idiom of this technology. Checked by `build.py check`. -->
| Concept (vocabulary) | Idiom |
|---|---|
| **value object** | `readonly record struct` or `record` with validation in the constructor; value equality from the compiler |
| **entity** | a class with an identifier type (`ResourceId`) and behaviour; equality by identifier |
| **aggregate** | a `sealed class` with private state, business methods instead of setters, `Version` for optimistic locking, `PullEvents()` |
| **variants** | an `abstract record` with a private constructor and nested `sealed record`s (a closed set) + `switch` |
| **operation result** | a closed hierarchy of records (`BlockResult.Blocked`, `.Conflict`, `.Disabled`) handled with `switch`; exceptions only for programmer errors |
| **event** | a `sealed record` in the past tense implementing `IDomainEvent` |
| **policy** | an interface with one method or a delegate (`Func<Order, Money>`) injected through the constructor |
| **repository** | an interface (port) in the domain project with `async` methods and `CancellationToken`; the adapter (EF Core, Dapper) in the infrastructure |
| **read model** | a separate `record` and query (Dapper, an EF Core `AsNoTracking` projection) bypassing the aggregate |
| **state machine** | the state as variants (`Free`, `Taken`, `Off`), transitions in a `switch` with patterns and `when` guards |
| **module** | a project (`.csproj`) or namespace with `internal` by default; dependencies between projects are guarded by references and architecture tests |

Tested implementations (amount, identifier, operation result, states, event, aggregate, repository port,
xUnit tests): `references/domain-building-blocks.md`.

## Version-dependent
Every threshold checked with a compiler (2026-10-23, SDK 10.0.113): the code does not compile in the earlier version,
and compiles in the given one; the default language version for the platform was checked too.
| Version | Changes relevant to this skill |
|---|---|
| C# 12 (.NET 8, LTS) | primary constructors in classes (`class P(string n)`), collection expressions (`int[] xs = [1, 2, 3]`), aliases of any types |
| C# 13 (.NET 9) | `params` collections (`params ReadOnlySpan<int>`, `params IEnumerable<T>`), the `System.Threading.Lock` type |
| C# 14 (.NET 10, LTS) | the `field` keyword in properties, `extension` blocks (extension properties and methods), null-conditional assignment `x?.Prop = v` |
.NET 11 with C# 15 (among others, union types) is at the release candidate stage; the release is planned for November 2026
[unverified: according to Visual Studio Magazine, 14.09.2026]. A project on .NET 11 → `detect_stack.py` reports
`SKILL_OUTDATED`, update per core-stack-sync.

## Example
Question: "Reserve should return success or a rejection". Result: `public BlockResult Block(string by, DateTimeOffset at)`
with `abstract record BlockResult { private BlockResult() {} sealed record Blocked(...); sealed record Conflict(string
BlockedBy); sealed record Disabled; }`. The caller: `result switch { BlockResult.Blocked => …, BlockResult.Conflict
c => …, BlockResult.Disabled => … }`. Adding a new variant shows every place to fill in when reviewing the
`switch`; a missing branch ends with an exception in `_ =>` (a programmer error). The full code with a test:
`references/domain-building-blocks.md`.

## Checklist
- [ ] `Nullable` on, warnings as errors, `dotnet format --verify-no-changes`
- [ ] no `double` for amounts, identifiers as types
- [ ] business rejections as a result, not exceptions; the `switch` handles every variant
- [ ] `async` with `CancellationToken` all the way, no `.Result`
- [ ] the syntax used matches the `TargetFramework` (the table above)

## Sources
- Microsoft Learn: "What's new in C# 12/13/14", "C# language versioning" (accessed 2026-10-23; thresholds checked
  with the compiler from SDK 8.0.132 and 10.0.113, Ubuntu 24.04 packages).
- .NET 11 RC: Visual Studio Magazine, ".NET 11 RC1 gets go-live support ahead of November launch" (14.09.2026).
Described in our own words.
