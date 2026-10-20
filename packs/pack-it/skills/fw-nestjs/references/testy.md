# Testy w NestJS

## 1. Piramida
| Poziom | Narzędzie | Co sprawdza | Czas |
|---|---|---|---|
| domena | Vitest / Jest, bez Nesta | reguły agregatów, obiekty wartości, polityki | ms |
| serwis / moduł | `Test.createTestingModule` + `overrideProvider` | serwis aplikacyjny z prawdziwym DI i podmienionymi adapterami | ~100 ms |
| e2e | `createNestApplication` + supertest + Testcontainers | HTTP → walidacja → serwis → baza | sekundy |

Większość testów na poziomie domeny i serwisu; e2e dla ścieżek krytycznych i reguł bezpieczeństwa.

## 2. Moduł testowy
```ts
const moduleRef = await Test.createTestingModule({ imports: [OrdersModule] })
  .overrideProvider(PaymentsClient).useValue({ charge: vi.fn() })
  .overrideGuard(AuthGuard).useValue({ canActivate: () => true })
  .compile();
```
- `overrideProvider(token)` przyjmuje `useValue`, `useClass` lub `useFactory`; analogicznie `overrideGuard`,
  `overridePipe`, `overrideInterceptor`, `overrideFilter`, `overrideModule`.
- `useMocker(factory)` tworzy zastępniki dla wszystkich brakujących providerów — wygodne, ale ukrywa błędy
  konfiguracji DI; używaj świadomie.
- Import całego modułu (`imports: [OrdersModule]`) sprawdza też jego `exports` i zależności; lista `providers`
  testuje tylko wybrane klasy.
- Provider o zakresie `REQUEST` lub `TRANSIENT` pobierasz przez `await moduleRef.resolve(Token)`, nie `get`.

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

it('odrzuca nieznane pole', () =>
  request(app.getHttpServer()).post('/orders').send({ sku: 'A-1', qty: 1, admin: true }).expect(400));
```
- Konfigurację z main.ts (pipe'y, filtry, prefiks, wersjonowanie) wydziel do funkcji `configureApp(app)`
  i wywołuj w obu miejscach — inaczej e2e testuje inną aplikację niż produkcyjna.
- Dla każdego chronionego endpointu: bez tokenu (401), zła rola (403), właściwa (2xx).

## 4. Testcontainers
- Paczka `@testcontainers/postgresql`, klasa `PostgreSqlContainer`; obraz z jawnym tagiem jak na produkcji
  (`postgres:17-alpine`), nie `latest`.
- Kontener startuje raz w global setup (Vitest `globalSetup`, Jest `globalSetup`), URL trafia do zmiennej
  środowiskowej, którą czyta `ConfigService`; migracje uruchamiasz przed testami.
- Izolacja danych: czyszczenie tabel (`TRUNCATE ... CASCADE`) przed testem albo osobny schemat na plik testowy.
- CI potrzebuje Dockera; bez niego testy e2e oznacz i uruchamiaj osobnym poleceniem (`test:e2e`).

## 5. Jest a Vitest
- `nest new` w v12: domyślnie ESM (`"type": "module"`) z Vitestem (`vitest run`, osobny vitest.config.e2e.ts);
  `--type cjs` → Jest z ts-jest (paczka `@nestjs/schematics` 12.0.8, dostęp 2026-10-19).
- Dekoratory i DI wymagają metadanych typów (`emitDecoratorMetadata`). Szablon `nestjs/typescript-starter` (master,
  dostęp 2026-10-20) ma Vitest 4 z `vite-tsconfig-paths`, bez `unplugin-swc` i bez `.swcrc`, a w tsconfig
  `emitDecoratorMetadata` i `experimentalDecorators` — metadane daje więc domyślny transformer Vite/Vitest; czy
  obsługuje `emitDecoratorMetadata` w każdej wersji Vite — [wtórne: ogłoszenie Vite 8 podaje obsługę wbudowaną].
  Gdy wstrzykiwanie w testach zwraca `undefined`, dodaj `unplugin-swc` albo jawne `@Inject(Token)`.
- Konfigurację runnera (mocki modułów, pokrycie, watch) opisują tool-vitest i tool-jest.

## 6. Pułapki
- SQLite „zamiast” PostgreSQL — inne typy, `ON CONFLICT`, blokady, sekwencje; błędy wychodzą dopiero na produkcji.
- Brak `app.close()` → otwarte połączenia i wiszący proces testów.
- `synchronize: true` w testach ukrywa brakujące migracje — testy uruchamiają te same migracje co produkcja.
- Czas: wstrzykuj zegar (provider `Clock`) zamiast `new Date()`; w testach stała data albo `vi.useFakeTimers()`.
