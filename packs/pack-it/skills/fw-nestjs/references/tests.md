# Tests in NestJS

## 1. Pyramid
| Level | Tool | What it checks | Time |
|---|---|---|---|
| domain | Vitest / Jest, without Nest | aggregate rules, value objects, policies | ms |
| service / module | `Test.createTestingModule` + `overrideProvider` | the application service with real DI and replaced adapters | ~100 ms |
| e2e | `createNestApplication` + supertest + Testcontainers | HTTP → validation → service → database | seconds |

Most tests at the domain and service level; e2e for critical paths and security rules.

## 2. Testing module
```ts
const moduleRef = await Test.createTestingModule({ imports: [OrdersModule] })
  .overrideProvider(PaymentsClient).useValue({ charge: vi.fn() })
  .overrideGuard(AuthGuard).useValue({ canActivate: () => true })
  .compile();
```
- `overrideProvider(token)` accepts `useValue`, `useClass` or `useFactory`; likewise `overrideGuard`,
  `overridePipe`, `overrideInterceptor`, `overrideFilter`, `overrideModule`.
- `useMocker(factory)` creates stand-ins for all missing providers — convenient, but it hides DI
  configuration errors; use it consciously.
- Importing the whole module (`imports: [OrdersModule]`) also checks its `exports` and dependencies; a `providers` list
  tests only the chosen classes.
- A provider with the `REQUEST` or `TRANSIENT` scope you get through `await moduleRef.resolve(Token)`, not `get`.

## 3. E2e
```ts
let app: INestApplication;
beforeAll(async () => {
  const moduleRef = await Test.createTestingModule({ imports: [AppModule] }).compile();
  app = moduleRef.createNestApplication();
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }));
  await app.init();
});
afterAll(() => app.close());

it('rejects an unknown field', () =>
  request(app.getHttpServer()).post('/orders').send({ sku: 'A-1', qty: 1, admin: true }).expect(400));
```
- Extract the configuration from main.ts (pipes, filters, prefix, versioning) into a `configureApp(app)` function
  and call it in both places — otherwise e2e tests a different application than the production one.
- For every protected endpoint: no token (401), wrong role (403), the right one (2xx).

## 4. Testcontainers
- The `@testcontainers/postgresql` package, the `PostgreSqlContainer` class; an image with an explicit tag as in production
  (`postgres:17-alpine`), not `latest`.
- The container starts once in global setup (Vitest `globalSetup`, Jest `globalSetup`), the URL goes into an environment
  variable that `ConfigService` reads; you run migrations before the tests.
- Data isolation: truncating tables (`TRUNCATE ... CASCADE`) before a test or a separate schema per test file.
- CI needs Docker; without it, mark the e2e tests and run them with a separate command (`test:e2e`).

## 5. Jest vs Vitest
- `nest new` in v12: ESM by default (`"type": "module"`) with Vitest (`vitest run`, a separate vitest.config.e2e.ts);
  `--type cjs` → Jest with ts-jest (the `@nestjs/schematics` 12.0.8 package, accessed 2026-10-19).
- Decorators and DI require type metadata (`emitDecoratorMetadata`). The `nestjs/typescript-starter` template (master,
  accessed 2026-10-20) has Vitest 4 with `vite-tsconfig-paths`, without `unplugin-swc` and without `.swcrc`, and in tsconfig
  `emitDecoratorMetadata` and `experimentalDecorators` — so the metadata comes from the default Vite/Vitest transformer; whether
  it supports `emitDecoratorMetadata` in every Vite version — [secondary: the Vite 8 announcement states built-in support].
  When injection in tests returns `undefined`, add `unplugin-swc` or an explicit `@Inject(Token)`.
- Runner configuration (module mocks, coverage, watch) is described by tool-vitest and tool-jest.

## 6. Pitfalls
- SQLite "instead of" PostgreSQL — different types, `ON CONFLICT`, locks, sequences; the errors only show up in production.
- No `app.close()` → open connections and a hanging test process.
- `synchronize: true` in tests hides missing migrations — tests run the same migrations as production.
- Time: inject a clock (a `Clock` provider) instead of `new Date()`; in tests a fixed date or `vi.useFakeTimers()`.
