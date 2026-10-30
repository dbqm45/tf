---
name: fw-nestjs
description: Użyj przy aplikacji NestJS — moduły i DI, kontrolery, walidacja DTO, konfiguracja, bezpieczeństwo, dane (TypeORM, Prisma), testy (@nestjs/testing, e2e).
metadata:
  katalog: "Użyj przy aplikacji NestJS — moduły i DI, kontrolery, walidacja DTO, konfiguracja, bezpieczeństwo, dane (TypeORM, Prisma), testy (@nestjs/testing, e2e). Nie do idiomów TypeScriptu (lang-typescript), modelowania domeny (ddd-*), ogólnego projektu API (be-api-design), baz danych niezależnie od frameworka (be-database) ani runnera testów (tool-jest, tool-vitest)."
  przeglad: "2027-01-20"
  slowa: "NestJS, Nest, @nestjs/core, @Module, @Injectable, @Controller, ValidationPipe, class-validator, DTO, ConfigModule, ConfigService, process.env, Test.createTestingModule, overrideProvider, createNestApplication, supertest, TypeORM, Prisma, Guard, Interceptor, Testcontainers, forwardRef"
---

# NestJS

## Kiedy stosować
- Kod, konfiguracja lub testy aplikacji NestJS (`@nestjs/core` w package.json), w tym migracja między wersjami.
- Idiomy TypeScriptu — lang-typescript; model domeny — ddd-tactical-design; kontrakt API — be-api-design; schemat
  i zapytania — be-database; uwierzytelnianie ogólnie — be-auth-security; metryki i ślady — ops-observability;
  konfiguracja runnera testów — tool-jest / tool-vitest.
- Poza zakresem: mikroserwisy i transporty, kolejki (BullMQ), CQRS, GraphQL.

## Procedura
1. **Ustal wersję** Nesta i Node.js (`python3 .claude/hooks/detect_stack.py`, package.json) oraz format modułów
   (`"type": "module"` = ESM). Stosuj API dostępne w tej wersji — tabela „Zależne od wersji”.
2. **Moduły:** moduł na obszar biznesowy (`OrdersModule`, `BillingModule`), nie na warstwę. `exports` tylko dla
   providerów, z których korzystają inne moduły. `forwardRef` to sygnał cyklu — wydziel wspólną część albo zastąp
   wywołanie zdarzeniem.
3. **Domena bez Nesta:** agregaty i obiekty wartości to zwykłe klasy TypeScriptu bez dekoratorów (lang-typescript).
   Nest żyje w adapterach (kontroler, repozytorium, moduł). Logika biznesowa w domenie, nie w kontrolerze.
4. **Kontroler i walidacja:** kontroler tłumaczy HTTP ↔ polecenie; bez `@Req()`/`@Res()` i ręcznych `if` na
   `req.body`. Wejście jako klasa DTO z dekoratorami `class-validator` (`@IsString()`, `@IsInt()`, `@Min()`),
   globalnie `app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }))`.
   Błędy domeny mapuje filtr wyjątków (`@Catch`) na status HTTP — format wg be-api-design.
5. **Dane** — wybór ORM, gdy projekt go jeszcze nie ma:
   - **TypeORM** (`@nestjs/typeorm`) — encje jako klasy z dekoratorami, repozytorium przez `@InjectRepository`;
     pasuje, gdy zespół zna wzorzec Data Mapper i chce trzymać model w kodzie.
   - **Prisma** — schemat w `schema.prisma`, typowany klient generowany z niego; pasuje przy nowym projekcie,
     gdy ważne są typy zapytań i prosta ścieżka migracji. Prisma 7: `PrismaService extends PrismaClient`
     z adapterem sterownika w konstruktorze (`super({ adapter: new PrismaPg({ connectionString }) })`,
     paczki `@prisma/adapter-pg` i `pg`), bez `OnModuleInit`/`$connect()`; generator `prisma-client`
     z obowiązkowym `output`, import klienta z wygenerowanej ścieżki, nie z `@prisma/client`.
   - MikroORM (Unit of Work, `@mikro-orm/nestjs`) i Drizzle (SQL-first, bez oficjalnej paczki Nesta) — gdy już są w projekcie.
   - Zawsze: migracje zamiast `synchronize: true` (TypeORM) i `prisma db push` poza prototypem; transakcja na
     granicy przypadku użycia (`dataSource.transaction(...)` / `prisma.$transaction(...)`); repozytorium jako
     adapter portu domeny.
6. **Konfiguracja:** `ConfigModule.forRoot({ isGlobal: true, validate })` (albo `validationSchema` — v12: Standard
   Schema, np. Zod) i `ConfigService` wstrzykiwany do providerów; bez `process.env` rozsianego po serwisach —
   aplikacja ma paść przy starcie, gdy brakuje zmiennej. Sekrety ze zmiennych środowiskowych, nigdy w repo.
7. **Bezpieczeństwo:** `helmet`, CORS z jawną listą originów, limit żądań `@nestjs/throttler` (`ThrottlerGuard`).
   Globalny guard uwierzytelniania (`{ provide: APP_GUARD, useClass: AuthGuard }`) i dekorator `@Public()` dla
   wyjątków — domyślnie wszystko wymaga uwierzytelnienia.
8. **Cykl życia:** `app.enableShutdownHooks()` (zamyka połączenia przy SIGTERM); health przez `@nestjs/terminus`
   (`TypeOrmHealthIndicator`, `PrismaHealthIndicator`) z osobnym liveness i readiness.
9. **Testy** (eng-testing, szczegóły `references/testy.md`):
   - domena — zwykłe testy jednostkowe bez Nesta;
   - serwis — `Test.createTestingModule({ providers: [OrdersService, OrdersRepository] })` i
     `.overrideProvider(OrdersRepository).useValue(fake)` zamiast ręcznego `new` z zależnościami;
   - e2e — `moduleRef.createNestApplication()`, te same globalne pipe'y co w main.ts, `await app.init()`, żądania
     przez `supertest`, `app.close()` po teście;
   - baza w testach = ta sama co na produkcji: Testcontainers (`@testcontainers/postgresql`,
     `PostgreSqlContainer`) zamiast SQLite w pamięci.
10. **Zakresy providerów:** domyślnie singleton. `Scope.REQUEST` propaguje się w górę — każdy provider zależny
    też staje się per żądanie (koszt wydajności); kontekst żądania raczej przez `AsyncLocalStorage` (np. `nestjs-cls`).

## Zasady
- Wstrzykiwanie przez konstruktor (`constructor(private readonly repo: OrdersRepository)`); tokeny dla interfejsów
  (`{ provide: ORDERS_REPOSITORY, useClass: TypeOrmOrdersRepository }` + `@Inject(ORDERS_REPOSITORY)`).
- Encja ORM ≠ DTO odpowiedzi: kontroler nie zwraca encji (wycieki pól, relacje).
- `transform: true` + jawne typy w DTO; parametry ścieżki przez `ParseIntPipe` / `ParseUUIDPipe`.
- Klient HTTP (`@nestjs/axios` albo `fetch`) zawsze z timeoutem.
- Logger Nesta (`new Logger(OrdersService.name)`) zamiast `console.log`.

## Przykład
**Wejście:** orders.service.spec.ts tworzy `new OrdersService(new OrdersRepository(null as any), ...)`, e2e na
SQLite w pamięci, produkcja na PostgreSQL.
**Wynik:**
```ts
const moduleRef = await Test.createTestingModule({
  providers: [OrdersService, OrdersRepository, PaymentsClient],
})
  .overrideProvider(OrdersRepository).useValue({ save: vi.fn() })   // jest.fn() w Jest
  .overrideProvider(PaymentsClient).useValue({ charge: vi.fn().mockResolvedValue({ ok: true }) })
  .compile();
const service = moduleRef.get(OrdersService);
```
E2e: kontener `new PostgreSqlContainer('postgres:17-alpine').start()` w global setup, URL do zmiennej
środowiskowej czytanej przez `ConfigService`, aplikacja przez `createNestApplication()` + `supertest`.
Dlaczego: moduł testowy sprawdza też konfigurację DI (brakujący provider = błąd testu); SQLite nie wyłapie różnic
dialektu (typy, `ON CONFLICT`, blokady). Więcej: `references/testy.md`.

## Zależne od wersji
| Wersja | Zmiany istotne dla tego skilla |
|---|---|
| 11.x | Express 5 w `@nestjs/platform-express` — wildcard w trasach nazwany (`/{*path}` zamiast `/*`); warstwa zgodności Nesta zamienia `/*` na `/{*path}` i loguje błąd, gdy nie potrafi (np. `*` w środku trasy). Linia utrzymywana pod tagiem npm `legacy` (11.2.7); nowy kod na 12.x |
| 12.0 | Paczki jako ESM; Node.js 20.19+ lub 22.12+ (pole `engines` mówi `>=20`). `nest new` domyślnie ESM z Vitestem, `--type cjs` → Jest; w ESM importy względne z `.js`. Hooki cyklu życia wywoływane wg poziomu w hierarchii modułów. `@nestjs/config`: `validationSchema` w formacie Standard Schema (Zod, ArkType; Joi 18+). `ConsoleLogger` domyślnie z parametrami strukturalnymi. Webpack w CLI przestarzały (rspack) |
| 12.2 | `ValidationPipe`: `validationError.target` domyślnie `false`. Express i Fastify: limity zagnieżdżenia pól (32) i indeksów tablic (1000) w body. `FileTypeValidator` dopasowuje pełny typ. `exclude()` w middleware wg dopasowania routera |

## Checklista przed oddaniem pracy
- [ ] moduły per obszar, `exports` minimalne, brak `forwardRef` bez uzasadnienia; logika w domenie bez dekoratorów
- [ ] globalny `ValidationPipe` (`whitelist`, `forbidNonWhitelisted`, `transform`), DTO z `class-validator`
- [ ] `ConfigModule` z walidacją, brak `process.env` w serwisach i sekretów w repo
- [ ] globalny guard + `@Public()`, helmet, CORS z listą, throttler; `enableShutdownHooks()` i health
- [ ] migracje zamiast `synchronize`/`db push`; transakcja na granicy przypadku użycia
- [ ] testy: `createTestingModule` + `overrideProvider`, e2e z `createNestApplication` + supertest, Testcontainers zamiast SQLite

## Materiały dodatkowe
- `references/testy.md` — piramida testów w NestJS, moduł testowy i nadpisywanie providerów, e2e, Testcontainers
  z global setup, Jest a Vitest (ESM/CJS), pułapki.

## Pojęcia domenowe w nestjs
<!-- Kontrakt: każde pojęcie ze słownika → idiom tej technologii. Sprawdzane przez `build.py check`. -->
| Pojęcie (słownik) | Idiom |
|---|---|
| **obiekt wartości** | klasa z `readonly` polami i walidacją w statycznej fabryce (lang-typescript); w TypeORM kolumna osadzona (`@Column(() => Money)`) lub transformer |
| **encja** | klasa domenowa z identyfikatorem; encja ORM (`@Entity`, model Prismy) w adapterze, mapowana na domenę |
| **agregat** | encja główna z kolumną wersji (`@VersionColumn` / pole `version` w Prismie); jedno repozytorium na agregat, zapis w jednej transakcji |
| **warianty** | unia rozróżnialna (`type: 'paid' \| 'cancelled'`); w DTO `@ValidateNested` + `@Type` z `discriminator` (class-transformer) |
| **wynik operacji** | unia `{ ok: true, value } \| { ok: false, error }` z serwisu; kontroler lub filtr wyjątków mapuje na status HTTP |
| **zdarzenie** | klasa zdarzenia emitowana przez `EventEmitter2` (`@nestjs/event-emitter`, `@OnEvent`); między usługami — outbox (be-messaging-outbox) |
| **polityka** | provider (interfejs + token) wstrzykiwany do serwisu aplikacyjnego |
| **repozytorium** | port (interfejs + token) w domenie, adapter TypeORM/Prisma w infrastrukturze rejestrowany w module |
| **read model** | osobny provider zapytań (SQL przez `dataSource.query` / `prisma.$queryRaw`) i DTO odpowiedzi |
| **maszyna stanów** | stan jako unia lub `enum` w agregacie, przejścia w metodach domeny |
| **moduł** | `@Module` per obszar; publiczne API = `exports`; cykle (`forwardRef`) traktuj jak błąd granicy |

## Źródła
Dostęp 2026-10-19; docs.nestjs.com niedostępne z sesji (proxy 403), więc fakty z paczek npm i repozytoriów.
- Wersje: `npm view` dla `@nestjs/core` (12.2.0, tagi `legacy` 11.2.7 i `old` 10.4.19), `@nestjs/cli` 12.0.9,
  `@nestjs/typeorm` 12.0.2, `@nestjs/config` 12.0.1, `@nestjs/terminus` 12.1.0, `@nestjs/throttler` 6.7.1.
- Definicje typów z paczek 12.2.0: `ValidationPipe` (`@nestjs/common`), `TestingModuleBuilder` z `overrideProvider`
  i `useValue`/`useClass`/`useFactory` (`@nestjs/testing`), `ConfigModuleOptions` (`validate`,
  `validationSchema: StandardSchemaV1`), `enableShutdownHooks` (`@nestjs/core`), wskaźniki zdrowia terminus.
- Zmiany: https://github.com/nestjs/nest/releases (v12.0.0, v12.2.0).
- Szablon `nest new` ESM: paczka `@nestjs/schematics` 12.0.8 (katalog lib/application/files/ts-esm).
- Prisma 7 w Nest: github.com/prisma/docs, `apps/docs/content/docs/guides/v7/frameworks/nestjs.mdx`;
  npm `@prisma/client` latest 7.10.1 (dostęp 2026-10-20).
- Wildcard: `packages/core/router/legacy-route-converter.ts` w nestjs/nest i `content/controllers.md`
  w nestjs/docs.nestjs.com (gałąź master); npm `@nestjs/core`: latest 12.2.0, legacy 11.2.7 (dostęp 2026-10-20).
- Node.js: https://nodejs.org/en/about/previous-releases; daty wydań [wtórne]: endoflife.ai.
Opisane własnymi słowami.
