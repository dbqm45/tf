---
name: fw-aspnet-core
description: Use for ASP.NET Core (.NET 8–10) — Minimal API, ProblemDetails, validation, OpenAPI, DI, WebApplicationFactory.
metadata:
  review: "2027-01-23"
  catalog: "Use when building and reviewing HTTP services in ASP.NET Core (.NET 8–10) — Minimal API and route groups, typed results (TypedResults, Results<…>), errors as ProblemDetails (application/problem+json), request validation (AddValidation in .NET 10), the OpenAPI document (AddOpenApi/MapOpenApi from .NET 9), dependency injection and lifetimes, configuration and options, mapping the domain result to HTTP, integration tests with WebApplicationFactory, differences between versions. Not for C# syntax and idioms (lang-csharp), technology-independent API design (be-api-design), authentication and authorization as a topic (be-auth-security), the database (be-database) or deployment (ops-*)."
  keywords: "ASP.NET Core, aspnetcore, Minimal API, minimal api, MapGet, MapPost, MapGroup, TypedResults, Results<>, ProblemDetails, problem+json, AddProblemDetails, walidacja w ASP.NET, AddValidation, OpenAPI w .NET, AddOpenApi, MapOpenApi, Swagger, WebApplicationFactory, test integracyjny ASP.NET, Mvc.Testing, kontrolery czy minimal api, DI scoped singleton, IOptions, appsettings, Kestrel, validation in ASP.NET, OpenAPI in .NET, ASP.NET integration test, controllers or minimal api"
---

# ASP.NET Core

## Procedure
1. **Platform version** from `TargetFramework` (table below) — the availability of validation and OpenAPI depends on it.
2. **Endpoints**: Minimal API with `MapGroup` per resource (controllers only when the project already uses them); the handler as
   a static method or a class, parameters bound explicitly (route, body, services).
3. **Typed result**: the handler returns `Results<Ok<T>, NotFound, ProblemHttpResult>` — the compiler guards the set of
   responses, and OpenAPI describes them. You map the domain result (lang-csharp) to HTTP in the handler, not in the domain.
4. **Errors**: `AddProblemDetails()` + `UseExceptionHandler()` + `UseStatusCodePages()`; a business rejection →
   `TypedResults.Problem(title, detail, statusCode)`. Note: `TypedResults.Conflict(new ProblemDetails {…})`
   sends plain `application/json`, not `application/problem+json` (checked by a test).
5. **Validation** (.NET 10): `AddValidation()` and `System.ComponentModel.DataAnnotations` attributes on request
   types (also on record parameters) → 400 with `ValidationProblem` without code in the handler. On .NET 8–9: manual
   validation in the handler or an endpoint filter. Business rules stay in the domain.
6. **OpenAPI** (.NET 9+): the `Microsoft.AspNetCore.OpenApi` package, `AddOpenApi()` and `MapOpenApi()` →
   `/openapi/v1.json`; operation names with `WithName`. On .NET 8: Swashbuckle or NSwag.
7. **Dependencies**: lifetimes — `Singleton` without per-request state, `Scoped` for a unit of work (e.g. `DbContext`),
   never `Scoped` injected into a `Singleton`; time through `TimeProvider`; configuration through `IOptions<T>`
   with validation at startup (`ValidateOnStart`), secrets from environment variables or a secret store.
8. **Integration tests**: `Microsoft.AspNetCore.Mvc.Testing`, `WebApplicationFactory<Program>` as an
   `IClassFixture`, `CreateClient()`; replacing services through `WithWebHostBuilder(b => b.ConfigureServices(…))`.
   On .NET 10 the test sees `Program` from top-level statements without adding `public partial class Program`
   (checked 2026-10-23); on older versions add that line.

## Example
`POST /resources/{id}/block` with `BlockRequest([Required, StringLength(50, MinimumLength = 2)] string By)`:
200 with `BlockResponse`, 404 for an unknown resource, 409 as `application/problem+json` for "taken by jan"
and "disabled", 400 from validation for `By = "a"`, the `BlockResource` operation in `/openapi/v1.json`. The code and 4
integration tests: `references/minimal-api.md`.

## Version-dependent
Thresholds checked by compilation 2026-10-23 (net8.0 and net10.0 from the SDK; net9.0 with reference packages from NuGet).
| Version | Changes relevant to this skill |
|---|---|
| .NET 8 (LTS) | Minimal API with `TypedResults` and `Results<…>`, `AddProblemDetails`; no `AddOpenApi` and no `AddValidation` |
| .NET 9 | built-in OpenAPI document: `AddOpenApi`, `MapOpenApi`; no `AddValidation` |
| .NET 10 (LTS) | validation in Minimal API: `AddValidation`; `Program` available to `WebApplicationFactory` without a partial declaration |
.NET 11 — release planned for November 2026 [unverified]; a project on .NET 11 → `SKILL_OUTDATED`
(core-stack-sync).

## Domain concepts in aspnet-core
<!-- Contract: every concept from the glossary → an idiom of this technology. Checked by `build.py check`. -->
| Concept (glossary) | Idiom |
|---|---|
| **value object** | a domain type (lang-csharp); in the request and response a separate DTO `record` mapped at the boundary |
| **entity** | a domain class; through the API you expose a DTO, not the entity (nor an EF Core entity) |
| **aggregate** | loaded from the repository in the handler, one business method per request, saved with the expected version → 409 on a concurrency conflict |
| **variants** | the domain result mapped in the handler with a `switch` onto `Results<…>` |
| **operation result** | `Results<Ok<T>, NotFound, ProblemHttpResult>`; a rejection → `TypedResults.Problem(statusCode: 409)` |
| **event** | collected from the aggregate (`PullEvents`) and saved in the outbox in the same transaction (be-messaging-outbox) |
| **policy** | a service in DI injected into the handler or the aggregate factory |
| **repository** | a port adapter registered in DI (`Scoped` with EF Core), injected into the handler |
| **read model** | a separate `GET` endpoint with a query that bypasses the aggregate (a projection, `AsNoTracking`) |
| **state machine** | transitions in the domain; the endpoint calls the transition method, a disallowed transition → 409 as ProblemDetails |
| **module** | a route group (`MapGroup`) and an extension method registering the module's services (`AddBooking()`) |

## Sources
- Microsoft Learn: Minimal APIs, "Handle errors in ASP.NET Core APIs", "Generate OpenAPI documents", "What's new in
  ASP.NET Core 9.0/10.0", "Integration tests in ASP.NET Core" (accessed 2026-10-23; behaviour checked on the
  example from `references/minimal-api.md`).
- RFC 9457 "Problem Details for HTTP APIs".
Described in our own words.
