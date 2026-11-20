# Tests in Spring Boot

## 1. Pyramid
| Level | Tool | What it checks | Time |
|---|---|---|---|
| domain | JUnit (5 or 6) + AssertJ, without Spring | aggregate rules, value objects, policies | ms |
| slice | `@WebMvcTest`, `@DataJpaTest`, `@JsonTest`, `@RestClientTest` | one layer with the real Spring configuration | ~1–3 s per context |
| integration | `@SpringBootTest` + Testcontainers | a flow through modules, transactions, events | seconds |
| contract | Spring Cloud Contract / Pact | compatibility with API consumers | — |

Most tests at the domain and slice level; `@SpringBootTest` for a few critical paths.

## 2. Slice tests
- `@WebMvcTest(OrderController.class)` — the controller, security filters, `@ControllerAdvice`, JSON converters.
  The application service as a `@MockitoBean`. You check the status, `ProblemDetail`, validation and authorization.
- `@DataJpaTest` — repositories, entities, queries. Since Boot 3.4 the default `Replace.NON_TEST` does not replace a database that
  comes from a container (Testcontainers, `@DynamicPropertySource`), so `@AutoConfigureTestDatabase(replace =
  Replace.NONE)` is usually unnecessary; in 3.0–3.3 the database was replaced with an embedded one and `Replace.NONE` is required
  (the `AutoConfigureTestDatabase` javadoc, release notes 3.4, accessed 2026-10-20). The test shows a different database than the container →
  add `Replace.NONE` explicitly. Every test in a transaction rolled back after the test.
- `@JsonTest` — serialization of DTOs and variants (`@JsonTypeInfo`).
- `@RestClientTest` — the HTTP client with `MockRestServiceServer`.

## 3. Testcontainers
```java
@TestConfiguration(proxyBeanMethods = false)
public class TestContainersConfig {
    @Bean @ServiceConnection
    PostgreSQLContainer<?> postgres() { return new PostgreSQLContainer<>("postgres:17-alpine"); }
}
```
- `@ServiceConnection` (Boot 3.1+) creates the connection details (`ConnectionDetails`) from the container — without
  `@DynamicPropertySource`.
- Testcontainers 2.x: artifacts with the `testcontainers-` prefix (e.g. `testcontainers-mysql`), classes in module packages
  (`org.testcontainers.mysql.MySQLContainer`; for PostgreSQL likewise `org.testcontainers.postgresql` [assumption]);
  JUnit 4 removed. When upgrading from 1.x fix the imports and dependencies.
- One container configuration class imported by the tests (`@Import`) → the same context and the same container.
- An image with an explicit tag (the version as in production), not `latest`.
- Development: `SpringApplication.from(App::main).with(TestContainersConfig.class).run(args)` in `src/test`
  runs the application with containers — from the IDE or `spring-boot:test-run` (Maven) / `bootTestRun` (Gradle)
  (`dev-services.adoc` in the Spring Boot main branch, accessed 2026-10-20); alternatively `spring-boot-docker-compose` with a Docker Compose file in the project directory.
- CI needs Docker (or a compatible environment); without it, tag the integration tests and run them separately.

## 4. Context cache
- Spring caches the context by the test configuration. Every different combination of `@MockitoBean`, profiles, `properties`
  or `@Import` = a new context (and new containers, if they are not shared).
- A common base class or a composed annotation for integration tests; mocks only where necessary.
- `@DirtiesContext` is a last resort — it usually hides shared state that has to be cleaned up.

## 5. Security
- `spring-security-test`: `@WithMockUser(roles = "ADMIN")`, `jwt()` / `oidcLogin()` from `SecurityMockMvcRequestPostProcessors`.
- For every endpoint: a test without authentication (401), with the wrong role (403), with the right one (2xx).
- A test that Actuator beyond `health` is not public.

## 6. Modules
```java
class ModularityTests {
    ApplicationModules modules = ApplicationModules.of(App.class);
    @Test void verifiesModularStructure() { modules.verify(); }
}
```
- Spring Modulith: `verify()` detects cycles and access to another module's internal types;
  `@ApplicationModuleTest` starts the context of one module; `Scenario` tests events between modules.
- Without Modulith: ArchUnit (`layeredArchitecture()`, `slices().should().beFreeOfCycles()`).

## 7. Pitfalls
- H2 "in PostgreSQL mode" is not PostgreSQL — different types, functions and locks.
- `@Transactional` on an integration test hides lazy loading errors and after-commit events — test the transactional
  flow without it and clean up the data explicitly.
- `@MockBean`/`@SpyBean` are deprecated since Boot 3.4 and removed in 4.0 — replace them with `@MockitoBean`/`@MockitoSpyBean`
  (they work on test class fields, not in `@Configuration` classes).
- Boot 4: `@SpringBootTest` by itself does not provide `MockMvc` — add `@AutoConfigureMockMvc`.
- Time: inject a `Clock` (bean) instead of `LocalDate.now()`; in tests `Clock.fixed(...)`.
