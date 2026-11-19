---
name: fw-spring-boot
description: Use for a Spring Boot application — modules, web and data, configuration, security, observability, tests (Testcontainers).
metadata:
  catalog: "Use for a Spring Boot application — module structure, the web and data layers, configuration, security, observability, tests (JUnit, slice tests, Testcontainers). Not for Java syntax and idioms (lang-java), domain modeling (ddd-*), general API design (be-api-design) or databases independent of the framework (be-database)."
  review: "2027-01-20"
  keywords: "Spring Boot, Spring, walidacja DTO, walidacja żądania w kontrolerze, @Valid, @Validated, Bean Validation, jakarta.validation, @RestController, @SpringBootTest, @MockBean, @MockitoBean, @DataJpaTest, @WebMvcTest, slice test, Testcontainers, @ServiceConnection, SecurityFilterChain, WebSecurityConfigurerAdapter, ProblemDetail, application.yml, @ConfigurationProperties, Actuator, Micrometer, RestClient, Spring Modulith, spring-boot-starter, DTO validation, request validation in the controller"
---

# Spring Boot

## When to use
- Code, configuration or tests of a Spring Boot application (pom.xml with `spring-boot-starter-parent`, the Gradle plugin
  `org.springframework.boot`), including migration between Boot versions.
- Java idioms — lang-java; the domain model — ddd-tactical-design; the API contract — be-api-design; the schema and queries —
  be-database; authentication in general — be-auth-security; metrics and traces in general — ops-observability.

## Procedure
1. **Establish the version** of Boot and Java (`python3 .claude/hooks/detect_stack.py`, pom.xml/build.gradle). Use only the API
   available in that version — the "Version-dependent" table.
2. **Structure:** a package per business module (`orders`, `billing`), not per layer (`controllers`, `services`).
   A module has a public API (facade, events), the rest is package-private. The boundaries are checked by the test
   `ApplicationModules.of(App.class).verify()` (Spring Modulith) or ArchUnit.
3. **A domain without Spring:** aggregates and value objects are plain Java (lang-java); Spring lives in the adapters
   (controller, repository, configuration). Business logic in the domain, not in a `@Service` or the controller.
4. **Web layer:** the controller translates HTTP ↔ a domain command; input validation with `@Valid` on the DTO record;
   errors as Problem Details (`ProblemDetail`, `spring.mvc.problemdetails.enabled=true` or
   a `@RestControllerAdvice` extending `ResponseEntityExceptionHandler`) — no custom maps with a message.
5. **Data:** a Spring Data repository as an adapter of a domain port; a transaction at the use case boundary
   (`@Transactional` on the application service, not on the controller or the repository); Flyway/Liquibase migrations,
   never `ddl-auto=update` outside a prototype. Events between modules after the commit
   (`@TransactionalEventListener` or an outbox — be-messaging-outbox).
6. **Configuration:** `@ConfigurationProperties` on a record with `@Validated` instead of scattered `@Value`s; secrets
   from environment variables or a secret manager, never in configuration files in the repo; profiles only for environment
   differences, not for logic.
7. **Security:** a `SecurityFilterChain` bean (lambda DSL) — `WebSecurityConfigurerAdapter` does not exist since
   Spring Security 6; by default everything requires authentication, exceptions explicit; method authorization
   with `@PreAuthorize`; you disable CSRF only for a stateless API with a token in a header.
8. **Observability:** Actuator exposing only `health`, `info`, `prometheus` (a separate port or protection);
   metrics and traces through Micrometer (Observation API); `health` with `liveness`/`readiness` groups for Kubernetes.
9. **Tests** (eng-testing, details in `references/tests.md`):
   - domain — JUnit without a Spring context (milliseconds);
   - slice tests: `@WebMvcTest` (controller + security, the service as a `@MockitoBean`), `@DataJpaTest`
     (repository), `@JsonTest`;
   - the database in tests = the same as in production: Testcontainers + `@ServiceConnection` (instead of H2 and a manual
     `@DynamicPropertySource`); containers in one `@TestConfiguration` class, shared between tests;
   - `@SpringBootTest` only for a few end-to-end flow tests;
   - `@MockBean`/`@SpyBean` → `@MockitoBean`/`@MockitoSpyBean` (in Boot 4 the old annotations are removed). Every different set of mocks
     creates a new context — keep the sets consistent so that the context cache works.
10. **Thread performance:** on Java 21+ `spring.threads.virtual.enabled=true` for I/O-bound work; check the database
    connection pool (virtual threads do not increase the number of connections) and `synchronized` blocks in old libraries.

## Rules
- Constructor injection (`final` fields), no `@Autowired` on fields; a single constructor needs no annotation.
- JPA entity ≠ API DTO: the controller does not return the entity (leaked fields, lazy loading, N+1).
- `open-in-view` disabled (`spring.jpa.open-in-view=false`); explicit data fetching (fetch join, projections).
- HTTP client: `RestClient` (synchronous) or an `@HttpExchange` interface; `RestTemplate` only in old code.
  Always connection and read timeouts.
- No `@SpringBootTest` for every test — the most common cause of slow CI.
- Dependency versions are managed by the Boot BOM; your own version overrides only with a justification (CVE) and a comment.

## Example
**Input:** a repository test on H2 with `@SpringBootTest` and `@MockBean`, production on PostgreSQL, Boot 3.4.
**Result:**
```java
@TestConfiguration(proxyBeanMethods = false)
class Containers {
    @Bean @ServiceConnection
    PostgreSQLContainer<?> postgres() { return new PostgreSQLContainer<>("postgres:17-alpine"); }
}

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import(Containers.class)
class OrderRepositoryTest {
    @Autowired OrderRepository repository;
    @MockitoBean OrderEventPublisher publisher; // @MockBean deprecated since Boot 3.4

    @Test
    void findsOrderByNumber() {
        repository.save(new Order("A-1"));
        assertThat(repository.findByNumber("A-1")).isPresent();
    }
}
```
More: `references/tests.md`.

## Version-dependent
| Version | Changes relevant to this skill |
|---|---|
| 3.x | Java 17+, Spring Framework 6, the `jakarta.*` namespace; `ProblemDetail` support (3.0); `@ServiceConnection` and Docker Compose support (3.1); `RestClient`, virtual threads (3.2); `@MockBean` deprecated in favour of `@MockitoBean` (3.4) (release notes 3.1, 3.2, 3.4 and issue #32634, accessed 2026-10-20). Free support for 3.5 ended 2026-06-30 [secondary] — new code on 4.x |
| 4.x | Java 17+, Spring Framework 7, Jakarta EE 11, Tomcat 11. Modularization: `spring-boot-<tech>` modules, `spring-boot-starter-<tech>` starters and test starters `spring-boot-starter-<tech>-test`; slice annotations in new packages (e.g. `org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest`). `@MockBean`/`@SpyBean` removed. `@SpringBootTest` no longer configures MockMvc or `TestRestTemplate` — `@AutoConfigureMockMvc`/`@AutoConfigureTestRestTemplate` or `RestTestClient`. Jackson 3 (`tools.jackson` packages), JSpecify instead of `org.springframework.lang`; Flyway/Liquibase require a starter; Undertow removed. HTTP clients: `@ImportHttpServices` for `@HttpExchange` interfaces |

## Checklist before handing over the work
- [ ] business logic in the domain (plain Java), Spring only in the adapters; module boundaries checked by a test
- [ ] API errors as Problem Details; input validated with `@Valid`
- [ ] `SecurityFilterChain` with the default "requires authentication"; Actuator restricted
- [ ] configuration through `@ConfigurationProperties` with validation; no secrets in `application*.yml`
- [ ] tests: domain without Spring, slice tests, Testcontainers with `@ServiceConnection`, no H2 as a production substitute
- [ ] no `@MockBean` on Boot 3.4+; no `RestTemplate` in new code; HTTP client timeouts

## Additional materials
- `references/tests.md` — the test pyramid in Spring Boot, slice tests, Testcontainers (`@ServiceConnection`,
  sharing, Docker Compose in development), the context cache, security and module tests.

## Domain concepts in spring-boot
<!-- Contract: every concept from the glossary → an idiom of this technology. Checked by `build.py check`. -->
| Concept (glossary) | Idiom |
|---|---|
| **value object** | a `record` with validation in the constructor; in JPA `@Embeddable` (records from Hibernate 6.2) or an `AttributeConverter` |
| **entity** | a JPA entity in the adapter or a domain class with minimal annotations; `equals` by identifier |
| **aggregate** | the root entity with `@Version` (optimistic locking); one repository per aggregate, the whole saved in one transaction |
| **variants** | a `sealed interface` + `record`s; in JSON `@JsonTypeInfo`/`@JsonSubTypes`, in the database a type column |
| **operation result** | a result returned from the application service, the controller maps the variants to an HTTP status and `ProblemDetail` |
| **event** | a `record` published through `ApplicationEventPublisher` or `AbstractAggregateRoot.registerEvent`; received with `@TransactionalEventListener` / `@ApplicationModuleListener` |
| **policy** | a bean (interface + implementation) injected into the application service or the aggregate factory |
| **repository** | a port in the domain, the adapter as a Spring Data interface (`JpaRepository`/`ListCrudRepository`) in infrastructure |
| **read model** | a Spring Data projection (an interface or a `record`), `JdbcClient` with SQL, a separate query endpoint |
| **state machine** | the state as a `sealed interface` or an `enum` in the aggregate, transitions in domain methods; Spring Statemachine only for complex, configurable flows |
| **module** | a top-level package under the `@SpringBootApplication` class; boundaries guarded by Spring Modulith (`verify()`) or ArchUnit |

## Sources
Accessed 2026-10-18; docs.spring.io unavailable from the session, so the documentation was read from the repository (branch 4.1.x).
- Spring Boot 4.0 Migration Guide — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
- Spring Boot 4.1.x documentation (testing, testcontainers, actuator, web/servlet, io/rest-client, system-requirements) —
  https://github.com/spring-projects/spring-boot/tree/4.1.x/documentation/spring-boot-docs
- Versions: Maven Central (spring-boot 4.1.1 and 3.5.16, testcontainers 2.0.5, junit-jupiter 6.1.3, spring-security 7.1.1,
  spring-modulith 2.1.1); https://spring.io/projects/spring-boot
- Support dates [secondary]: endoflife.date (GitHub repository, file products/spring-boot.md).
- Testcontainers 2.0 release notes — https://github.com/testcontainers/testcontainers-java/releases/tag/2.0.0
Described in our own words.
