---
name: fw-nestjs
description: Use for a NestJS application — modules and DI, controllers, DTO validation, security, TypeORM/Prisma, e2e tests.
metadata:
  catalog: "Use for a NestJS application — modules and DI, controllers, DTO validation, configuration, security, data (TypeORM, Prisma), tests (@nestjs/testing, e2e). Not for TypeScript idioms (lang-typescript), domain modeling (ddd-*), general API design (be-api-design), databases independent of the framework (be-database) or the test runner (tool-jest, tool-vitest)."
  review: "2027-01-20"
  keywords: "NestJS, Nest, @nestjs/core, @Module, @Injectable, @Controller, ValidationPipe, class-validator, DTO, ConfigModule, ConfigService, process.env, Test.createTestingModule, overrideProvider, createNestApplication, supertest, TypeORM, Prisma, Guard, Interceptor, Testcontainers, forwardRef"
---

# NestJS

## When to use
- Code, configuration or tests of a NestJS application (`@nestjs/core` in package.json), including migration between versions.
- TypeScript idioms — lang-typescript; the domain model — ddd-tactical-design; the API contract — be-api-design; the schema
  and queries — be-database; authentication in general — be-auth-security; metrics and traces — ops-observability;
  test runner configuration — tool-jest / tool-vitest.
- Out of scope: microservices and transports, queues (BullMQ), CQRS, GraphQL.

## Procedure
1. **Establish the version** of Nest and Node.js (`python3 .claude/hooks/detect_stack.py`, package.json) and the module format
   (`"type": "module"` = ESM). Use the API available in that version — the "Version-dependent" table.
2. **Modules:** a module per business area (`OrdersModule`, `BillingModule`), not per layer. `exports` only for
   providers that other modules use. `forwardRef` is a signal of a cycle — extract the shared part or replace the
   call with an event.
3. **A domain without Nest:** aggregates and value objects are plain TypeScript classes without decorators (lang-typescript).
   Nest lives in the adapters (controller, repository, module). Business logic in the domain, not in the controller.
4. **Controller and validation:** the controller translates HTTP ↔ command; no `@Req()`/`@Res()` and no manual `if`s on
   `req.body`. Input as a DTO class with `class-validator` decorators (`@IsString()`, `@IsInt()`, `@Min()`),
   globally `app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }))`.
   An exception filter (`@Catch`) maps domain errors to an HTTP status — the format per be-api-design.
5. **Data** — choosing an ORM when the project does not have one yet:
   - **TypeORM** (`@nestjs/typeorm`) — entities as classes with decorators, the repository through `@InjectRepository`;
     fits when the team knows the Data Mapper pattern and wants to keep the model in code.
   - **Prisma** — the schema in `schema.prisma`, a typed client generated from it; fits a new project
     when query types and a simple migration path matter. Prisma 7: `PrismaService extends PrismaClient`
     with a driver adapter in the constructor (`super({ adapter: new PrismaPg({ connectionString }) })`,
     the `@prisma/adapter-pg` and `pg` packages), without `OnModuleInit`/`$connect()`; the `prisma-client` generator
     with a mandatory `output`, the client imported from the generated path, not from `@prisma/client`.
   - MikroORM (Unit of Work, `@mikro-orm/nestjs`) and Drizzle (SQL-first, no official Nest package) — when they are already in the project.
   - Always: migrations instead of `synchronize: true` (TypeORM) and `prisma db push` outside a prototype; a transaction at the
     use case boundary (`dataSource.transaction(...)` / `prisma.$transaction(...)`); the repository as an
     adapter of a domain port.
6. **Configuration:** `ConfigModule.forRoot({ isGlobal: true, validate })` (or `validationSchema` — v12: Standard
   Schema, e.g. Zod) and `ConfigService` injected into providers; no `process.env` scattered across services —
   the application must fail at startup when a variable is missing. Secrets from environment variables, never in the repo.
7. **Security:** `helmet`, CORS with an explicit list of origins, rate limiting with `@nestjs/throttler` (`ThrottlerGuard`).
   A global authentication guard (`{ provide: APP_GUARD, useClass: AuthGuard }`) and a `@Public()` decorator for
   exceptions — by default everything requires authentication.
8. **Lifecycle:** `app.enableShutdownHooks()` (closes connections on SIGTERM); health through `@nestjs/terminus`
   (`TypeOrmHealthIndicator`, `PrismaHealthIndicator`) with separate liveness and readiness.
9. **Tests** (eng-testing, details in `references/tests.md`):
   - domain — plain unit tests without Nest;
   - service — `Test.createTestingModule({ providers: [OrdersService, OrdersRepository] })` and
     `.overrideProvider(OrdersRepository).useValue(fake)` instead of a manual `new` with dependencies;
   - e2e — `moduleRef.createNestApplication()`, the same global pipes as in main.ts, `await app.init()`, requests
     through `supertest`, `app.close()` after the test;
   - the database in tests = the same as in production: Testcontainers (`@testcontainers/postgresql`,
     `PostgreSqlContainer`) instead of in-memory SQLite.
10. **Provider scopes:** singleton by default. `Scope.REQUEST` propagates upwards — every dependent provider
    also becomes per-request (a performance cost); request context rather through `AsyncLocalStorage` (e.g. `nestjs-cls`).

## Rules
- Constructor injection (`constructor(private readonly repo: OrdersRepository)`); tokens for interfaces
  (`{ provide: ORDERS_REPOSITORY, useClass: TypeOrmOrdersRepository }` + `@Inject(ORDERS_REPOSITORY)`).
- ORM entity ≠ response DTO: the controller does not return the entity (leaked fields, relations).
- `transform: true` + explicit types in DTOs; path parameters through `ParseIntPipe` / `ParseUUIDPipe`.
- The HTTP client (`@nestjs/axios` or `fetch`) always with a timeout.
- The Nest logger (`new Logger(OrdersService.name)`) instead of `console.log`.

## Example
**Input:** orders.service.spec.ts creates `new OrdersService(new OrdersRepository(null as any), ...)`, e2e on
in-memory SQLite, production on PostgreSQL.
**Result:**
```ts
const moduleRef = await Test.createTestingModule({
  providers: [OrdersService, OrdersRepository, PaymentsClient],
})
  .overrideProvider(OrdersRepository).useValue({ save: vi.fn() })   // jest.fn() in Jest
  .overrideProvider(PaymentsClient).useValue({ charge: vi.fn().mockResolvedValue({ ok: true }) })
  .compile();
const service = moduleRef.get(OrdersService);
```
E2e: the container `new PostgreSqlContainer('postgres:17-alpine').start()` in global setup, the URL into an environment
variable read by `ConfigService`, the application through `createNestApplication()` + `supertest`.
Why: the testing module also checks the DI configuration (a missing provider = a test failure); SQLite will not catch dialect
differences (types, `ON CONFLICT`, locks). More: `references/tests.md`.

## Version-dependent
| Version | Changes relevant to this skill |
|---|---|
| 11.x | Express 5 in `@nestjs/platform-express` — the wildcard in routes is named (`/{*path}` instead of `/*`); Nest's compatibility layer converts `/*` to `/{*path}` and logs an error when it cannot (e.g. `*` in the middle of a route). The line is maintained under the npm tag `legacy` (11.2.7); new code on 12.x |
| 12.0 | Packages as ESM; Node.js 20.19+ or 22.12+ (the `engines` field says `>=20`). `nest new` defaults to ESM with Vitest, `--type cjs` → Jest; in ESM relative imports with `.js`. Lifecycle hooks called by level in the module hierarchy. `@nestjs/config`: `validationSchema` in the Standard Schema format (Zod, ArkType; Joi 18+). `ConsoleLogger` with structured parameters by default. Webpack in the CLI deprecated (rspack) |
| 12.2 | `ValidationPipe`: `validationError.target` defaults to `false`. Express and Fastify: limits on field nesting (32) and array indices (1000) in the body. `FileTypeValidator` matches the full type. `exclude()` in middleware per router matching |

## Checklist before handing over the work
- [ ] modules per area, minimal `exports`, no `forwardRef` without a justification; logic in the domain without decorators
- [ ] a global `ValidationPipe` (`whitelist`, `forbidNonWhitelisted`, `transform`), DTOs with `class-validator`
- [ ] `ConfigModule` with validation, no `process.env` in services and no secrets in the repo
- [ ] a global guard + `@Public()`, helmet, CORS with a list, throttler; `enableShutdownHooks()` and health
- [ ] migrations instead of `synchronize`/`db push`; a transaction at the use case boundary
- [ ] tests: `createTestingModule` + `overrideProvider`, e2e with `createNestApplication` + supertest, Testcontainers instead of SQLite

## Additional materials
- `references/tests.md` — the test pyramid in NestJS, the testing module and overriding providers, e2e, Testcontainers
  with global setup, Jest vs Vitest (ESM/CJS), pitfalls.

## Domain concepts in nestjs
<!-- Contract: every concept from the glossary → an idiom of this technology. Checked by `build.py check`. -->
| Concept (glossary) | Idiom |
|---|---|
| **value object** | a class with `readonly` fields and validation in a static factory (lang-typescript); in TypeORM an embedded column (`@Column(() => Money)`) or a transformer |
| **entity** | a domain class with an identifier; the ORM entity (`@Entity`, a Prisma model) in the adapter, mapped onto the domain |
| **aggregate** | the root entity with a version column (`@VersionColumn` / a `version` field in Prisma); one repository per aggregate, saved in one transaction |
| **variants** | a discriminated union (`type: 'paid' \| 'cancelled'`); in a DTO `@ValidateNested` + `@Type` with `discriminator` (class-transformer) |
| **operation result** | a union `{ ok: true, value } \| { ok: false, error }` from the service; the controller or an exception filter maps it to an HTTP status |
| **event** | an event class emitted through `EventEmitter2` (`@nestjs/event-emitter`, `@OnEvent`); between services — an outbox (be-messaging-outbox) |
| **policy** | a provider (interface + token) injected into the application service |
| **repository** | a port (interface + token) in the domain, a TypeORM/Prisma adapter in infrastructure registered in the module |
| **read model** | a separate query provider (SQL through `dataSource.query` / `prisma.$queryRaw`) and a response DTO |
| **state machine** | the state as a union or an `enum` in the aggregate, transitions in domain methods |
| **module** | `@Module` per area; the public API = `exports`; treat cycles (`forwardRef`) as a boundary error |

## Sources
Accessed 2026-10-19; docs.nestjs.com unavailable from the session (proxy 403), so the facts come from npm packages and repositories.
- Versions: `npm view` for `@nestjs/core` (12.2.0, tags `legacy` 11.2.7 and `old` 10.4.19), `@nestjs/cli` 12.0.9,
  `@nestjs/typeorm` 12.0.2, `@nestjs/config` 12.0.1, `@nestjs/terminus` 12.1.0, `@nestjs/throttler` 6.7.1.
- Type definitions from the 12.2.0 packages: `ValidationPipe` (`@nestjs/common`), `TestingModuleBuilder` with `overrideProvider`
  and `useValue`/`useClass`/`useFactory` (`@nestjs/testing`), `ConfigModuleOptions` (`validate`,
  `validationSchema: StandardSchemaV1`), `enableShutdownHooks` (`@nestjs/core`), the terminus health indicators.
- Changes: https://github.com/nestjs/nest/releases (v12.0.0, v12.2.0).
- The ESM `nest new` template: the `@nestjs/schematics` 12.0.8 package (directory lib/application/files/ts-esm).
- Prisma 7 in Nest: github.com/prisma/docs, `apps/docs/content/docs/guides/v7/frameworks/nestjs.mdx`;
  npm `@prisma/client` latest 7.10.1 (accessed 2026-10-20).
- Wildcard: `packages/core/router/legacy-route-converter.ts` in nestjs/nest and `content/controllers.md`
  in nestjs/docs.nestjs.com (master branch); npm `@nestjs/core`: latest 12.2.0, legacy 11.2.7 (accessed 2026-10-20).
- Node.js: https://nodejs.org/en/about/previous-releases; release dates [secondary]: https://endoflife.date/nodejs (accessed 2026-11-23).
Described in our own words.
