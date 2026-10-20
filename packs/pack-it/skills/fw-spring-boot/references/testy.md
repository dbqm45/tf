# Testy w Spring Boot

## 1. Piramida
| Poziom | Narzędzie | Co sprawdza | Czas |
|---|---|---|---|
| domena | JUnit (5 lub 6) + AssertJ, bez Springa | reguły agregatów, obiekty wartości, polityki | ms |
| slice | `@WebMvcTest`, `@DataJpaTest`, `@JsonTest`, `@RestClientTest` | jedna warstwa z prawdziwą konfiguracją Springa | ~1–3 s na kontekst |
| integracja | `@SpringBootTest` + Testcontainers | przepływ przez moduły, transakcje, zdarzenia | sekundy |
| kontrakt | Spring Cloud Contract / Pact | zgodność z konsumentami API | — |

Większość testów na poziomie domeny i slice; `@SpringBootTest` dla kilku ścieżek krytycznych.

## 2. Slice testy
- `@WebMvcTest(OrderController.class)` — kontroler, filtry bezpieczeństwa, `@ControllerAdvice`, konwertery JSON.
  Serwis aplikacyjny jako `@MockitoBean`. Sprawdzasz status, `ProblemDetail`, walidację i autoryzację.
- `@DataJpaTest` — repozytoria, encje, zapytania. Od Boot 3.4 domyślne `Replace.NON_TEST` nie podmienia bazy, która
  pochodzi z kontenera (Testcontainers, `@DynamicPropertySource`), więc `@AutoConfigureTestDatabase(replace =
  Replace.NONE)` zwykle jest zbędne; w 3.0–3.3 baza była podmieniana na wbudowaną i `Replace.NONE` jest wymagane
  (javadoc `AutoConfigureTestDatabase`, release notes 3.4, dostęp 2026-10-20). Test pokazuje inną bazę niż kontener →
  dodaj `Replace.NONE` jawnie. Każdy test w transakcji wycofywanej po teście.
- `@JsonTest` — serializacja DTO i wariantów (`@JsonTypeInfo`).
- `@RestClientTest` — klient HTTP z `MockRestServiceServer`.

## 3. Testcontainers
```java
@TestConfiguration(proxyBeanMethods = false)
public class TestContainersConfig {
    @Bean @ServiceConnection
    PostgreSQLContainer<?> postgres() { return new PostgreSQLContainer<>("postgres:17-alpine"); }
}
```
- `@ServiceConnection` (Boot 3.1+) tworzy szczegóły połączenia (`ConnectionDetails`) z kontenera — bez
  `@DynamicPropertySource`.
- Testcontainers 2.x: artefakty z prefiksem `testcontainers-` (np. `testcontainers-mysql`), klasy w pakietach modułu
  (`org.testcontainers.mysql.MySQLContainer`; dla PostgreSQL analogicznie `org.testcontainers.postgresql` [założenie]);
  JUnit 4 usunięty. Przy aktualizacji z 1.x popraw importy i zależności.
- Jedna klasa konfiguracji kontenerów importowana przez testy (`@Import`) → ten sam kontekst i ten sam kontener.
- Obraz z jawnym tagiem (wersja jak na produkcji), nie `latest`.
- Dewelopment: `SpringApplication.from(App::main).with(TestContainersConfig.class).run(args)` w `src/test`
  uruchamia aplikację z kontenerami — z IDE albo `spring-boot:test-run` (Maven) / `bootTestRun` (Gradle)
  (`dev-services.adoc` w gałęzi main Spring Boot, dostęp 2026-10-20); alternatywnie `spring-boot-docker-compose` z plikiem Docker Compose w katalogu projektu.
- CI potrzebuje Dockera (lub zgodnego środowiska); bez niego testy integracyjne oznacz tagiem i uruchamiaj osobno.

## 4. Cache kontekstu
- Spring buforuje kontekst po konfiguracji testu. Każda inna kombinacja `@MockitoBean`, profili, `properties`
  albo `@Import` = nowy kontekst (i nowe kontenery, jeśli nie są współdzielone).
- Wspólna klasa bazowa lub adnotacja złożona dla testów integracyjnych; mocki tylko tam, gdzie konieczne.
- `@DirtiesContext` to ostateczność — zwykle ukrywa współdzielony stan, który trzeba sprzątać.

## 5. Bezpieczeństwo
- `spring-security-test`: `@WithMockUser(roles = "ADMIN")`, `jwt()` / `oidcLogin()` z `SecurityMockMvcRequestPostProcessors`.
- Dla każdego endpointu: test bez uwierzytelnienia (401), z niewłaściwą rolą (403), z właściwą (2xx).
- Test, że Actuator poza `health` nie jest publiczny.

## 6. Moduły
```java
class ModularityTests {
    ApplicationModules modules = ApplicationModules.of(App.class);
    @Test void verifiesModularStructure() { modules.verify(); }
}
```
- Spring Modulith: `verify()` wykrywa cykle i dostęp do typów wewnętrznych innego modułu;
  `@ApplicationModuleTest` uruchamia kontekst jednego modułu; `Scenario` testuje zdarzenia między modułami.
- Bez Modulith: ArchUnit (`layeredArchitecture()`, `slices().should().beFreeOfCycles()`).

## 7. Pułapki
- H2 „w trybie PostgreSQL” to nie PostgreSQL — inne typy, funkcje i blokady.
- `@Transactional` na teście integracyjnym ukrywa błędy leniwego ładowania i zdarzeń po commicie — przepływ
  transakcyjny testuj bez niego i sprzątaj dane jawnie.
- `@MockBean`/`@SpyBean` są przestarzałe od Boot 3.4 i usunięte w 4.0 — zastąp `@MockitoBean`/`@MockitoSpyBean`
  (działają na polach klasy testu, nie w klasach `@Configuration`).
- Boot 4: `@SpringBootTest` sam nie daje `MockMvc` — dodaj `@AutoConfigureMockMvc`.
- Czas: wstrzykuj `Clock` (bean) zamiast `LocalDate.now()`; w testach `Clock.fixed(...)`.
