---
name: fw-spring-boot
description: Użyj przy aplikacji Spring Boot — struktura modułów, warstwa web i danych, konfiguracja, bezpieczeństwo, obserwowalność, testy (JUnit, slice testy, Testcontainers).
metadata:
  katalog: "Użyj przy aplikacji Spring Boot — struktura modułów, warstwa web i danych, konfiguracja, bezpieczeństwo, obserwowalność, testy (JUnit, slice testy, Testcontainers). Nie do składni i idiomów Javy (lang-java), modelowania domeny (ddd-*), ogólnego projektu API (be-api-design) ani baz danych niezależnie od frameworka (be-database)."
  przeglad: 2027-01-20
  slowa: "Spring Boot, Spring, @SpringBootTest, @MockBean, @MockitoBean, @DataJpaTest, @WebMvcTest, slice test, Testcontainers, @ServiceConnection, SecurityFilterChain, WebSecurityConfigurerAdapter, ProblemDetail, application.yml, @ConfigurationProperties, Actuator, Micrometer, RestClient, Spring Modulith, spring-boot-starter"
---

# Spring Boot

## Kiedy stosować
- Kod, konfiguracja lub testy aplikacji na Spring Boot (pom.xml z `spring-boot-starter-parent`, plugin Gradle
  `org.springframework.boot`), w tym migracja między wersjami Boota.
- Idiomy Javy — lang-java; model domeny — ddd-tactical-design; kontrakt API — be-api-design; schemat i zapytania —
  be-database; uwierzytelnianie ogólnie — be-auth-security; metryki i ślady ogólnie — ops-observability.

## Procedura
1. **Ustal wersję** Boota i Javy (`python3 .claude/hooks/detect_stack.py`, pom.xml/build.gradle). Stosuj tylko API
   dostępne w tej wersji — tabela „Zależne od wersji”.
2. **Struktura:** pakiet na moduł biznesowy (`orders`, `billing`), nie na warstwę (`controllers`, `services`).
   Moduł ma publiczne API (fasada, zdarzenia), reszta package-private. Granice sprawdza test
   `ApplicationModules.of(App.class).verify()` (Spring Modulith) albo ArchUnit.
3. **Domena bez Springa:** agregaty i obiekty wartości to czysta Java (lang-java); Spring żyje w adapterach
   (kontroler, repozytorium, konfiguracja). Logika biznesowa w domenie, nie w `@Service` ani kontrolerze.
4. **Warstwa web:** kontroler tłumaczy HTTP ↔ polecenie domenowe; walidacja wejścia `@Valid` na rekordzie DTO;
   błędy jako Problem Details (`ProblemDetail`, `spring.mvc.problemdetails.enabled=true` albo
   `@RestControllerAdvice` rozszerzający `ResponseEntityExceptionHandler`) — bez własnych map z komunikatem.
5. **Dane:** Spring Data repozytorium jako adapter portu domeny; transakcja na granicy przypadku użycia
   (`@Transactional` na serwisie aplikacyjnym, nie na kontrolerze ani repozytorium); migracje Flyway/Liquibase,
   nigdy `ddl-auto=update` poza prototypem. Zdarzenia między modułami po commicie
   (`@TransactionalEventListener` albo outbox — be-messaging-outbox).
6. **Konfiguracja:** `@ConfigurationProperties` na rekordzie z `@Validated` zamiast rozsianych `@Value`; sekrety
   z zmiennych środowiskowych lub menedżera sekretów, nigdy w plikach konfiguracji w repo; profile tylko dla różnic
   środowiska, nie dla logiki.
7. **Bezpieczeństwo:** bean `SecurityFilterChain` (lambda DSL) — `WebSecurityConfigurerAdapter` nie istnieje od
   Spring Security 6; domyślnie wszystko wymaga uwierzytelnienia, wyjątki jawnie; autoryzacja metod
   `@PreAuthorize`; CSRF wyłączasz tylko dla API bezstanowego z tokenem w nagłówku.
8. **Obserwowalność:** Actuator z wystawionymi tylko `health`, `info`, `prometheus` (osobny port lub ochrona);
   metryki i ślady przez Micrometer (Observation API); `health` z grupami `liveness`/`readiness` dla Kubernetesa.
9. **Testy** (eng-testing, szczegóły `references/testy.md`):
   - domena — JUnit bez kontekstu Springa (milisekundy);
   - slice testy: `@WebMvcTest` (kontroler + bezpieczeństwo, serwis jako `@MockitoBean`), `@DataJpaTest`
     (repozytorium), `@JsonTest`;
   - baza w testach = ta sama co na produkcji: Testcontainers + `@ServiceConnection` (zamiast H2 i ręcznego
     `@DynamicPropertySource`); kontenery w jednej klasie `@TestConfiguration`, współdzielone między testami;
   - `@SpringBootTest` tylko dla kilku testów przepływu end-to-end;
   - `@MockBean`/`@SpyBean` → `@MockitoBean`/`@MockitoSpyBean` (w Boot 4 stare adnotacje usunięte). Każdy inny zestaw mocków
     tworzy nowy kontekst — trzymaj zestawy spójne, żeby cache kontekstu działał.
10. **Wydajność wątków:** na Javie 21+ `spring.threads.virtual.enabled=true` dla I/O-bound; sprawdź pulę połączeń
    bazy (wirtualne wątki nie zwiększają liczby połączeń) i bloki `synchronized` w starych bibliotekach.

## Zasady
- Wstrzykiwanie przez konstruktor (pola `final`), bez `@Autowired` na polach; jeden konstruktor nie wymaga adnotacji.
- Encja JPA ≠ DTO API: kontroler nie zwraca encji (wycieki pól, leniwe ładowanie, N+1).
- `open-in-view` wyłączone (`spring.jpa.open-in-view=false`); pobieranie danych jawne (fetch join, projekcje).
- Klient HTTP: `RestClient` (synchronicznie) albo interfejs `@HttpExchange`; `RestTemplate` tylko w starym kodzie.
  Zawsze timeouty połączenia i odczytu.
- Bez `@SpringBootTest` dla każdego testu — to najczęstsza przyczyna wolnego CI.
- Wersje zależności zarządza BOM Boota; własne nadpisania wersji tylko z uzasadnieniem (CVE) i komentarzem.

## Przykład
**Wejście:** test repozytorium na H2 z `@SpringBootTest` i `@MockBean`, produkcja na PostgreSQL, Boot 3.4.
**Wynik:**
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
    @MockitoBean OrderEventPublisher publisher; // @MockBean przestarzałe od Boot 3.4

    @Test
    void findsOrderByNumber() {
        repository.save(new Order("A-1"));
        assertThat(repository.findByNumber("A-1")).isPresent();
    }
}
```
Dlaczego: H2 nie wyłapie różnic dialektu (typy, `ON CONFLICT`, sekwencje); slice ładuje tylko warstwę JPA;
`@ServiceConnection` sam ustawia URL i dane logowania kontenera. Więcej: `references/testy.md`.

## Zależne od wersji
| Wersja | Zmiany istotne dla tego skilla |
|---|---|
| 3.x | Java 17+, Spring Framework 6, przestrzeń `jakarta.*`; obsługa `ProblemDetail` (3.0); `@ServiceConnection` i obsługa Docker Compose (3.1); `RestClient`, wirtualne wątki (3.2); `@MockBean` zdeprecjonowany na rzecz `@MockitoBean` (3.4) (release notes 3.1, 3.2, 3.4 i issue #32634, dostęp 2026-10-20). Darmowe wsparcie 3.5 skończyło się 2026-06-30 [wtórne] — nowy kod na 4.x |
| 4.x | Java 17+, Spring Framework 7, Jakarta EE 11, Tomcat 11. Modularyzacja: moduły `spring-boot-<tech>`, startery `spring-boot-starter-<tech>` i testowe `spring-boot-starter-<tech>-test`; adnotacje slice w nowych pakietach (np. `org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest`). `@MockBean`/`@SpyBean` usunięte. `@SpringBootTest` nie konfiguruje już MockMvc ani `TestRestTemplate` — `@AutoConfigureMockMvc`/`@AutoConfigureTestRestTemplate` albo `RestTestClient`. Jackson 3 (pakiety `tools.jackson`), JSpecify zamiast `org.springframework.lang`; Flyway/Liquibase wymagają startera; Undertow usunięty. Klienci HTTP: `@ImportHttpServices` dla interfejsów `@HttpExchange` |

## Checklista przed oddaniem pracy
- [ ] logika biznesowa w domenie (czysta Java), Spring tylko w adapterach; granice modułów sprawdzone testem
- [ ] błędy API jako Problem Details; wejście walidowane `@Valid`
- [ ] `SecurityFilterChain` z domyślnym „wymaga uwierzytelnienia”; Actuator ograniczony
- [ ] konfiguracja przez `@ConfigurationProperties` z walidacją; brak sekretów w `application*.yml`
- [ ] testy: domena bez Springa, slice testy, Testcontainers z `@ServiceConnection`, brak H2 jako zamiennika produkcji
- [ ] brak `@MockBean` na Boot 3.4+; brak `RestTemplate` w nowym kodzie; timeouty klientów HTTP

## Materiały dodatkowe
- `references/testy.md` — piramida testów w Spring Boot, slice testy, Testcontainers (`@ServiceConnection`,
  współdzielenie, Docker Compose w dewelopmencie), cache kontekstu, testy bezpieczeństwa i modułów.

## Pojęcia domenowe w spring-boot
<!-- Kontrakt: każde pojęcie ze słownika → idiom tej technologii. Sprawdzane przez `build.py check`. -->
| Pojęcie (słownik) | Idiom |
|---|---|
| **obiekt wartości** | `record` z walidacją w konstruktorze; w JPA `@Embeddable` (record od Hibernate 6.2) albo konwerter `AttributeConverter` |
| **encja** | encja JPA w adapterze albo klasa domenowa z minimalnymi adnotacjami; `equals` po identyfikatorze |
| **agregat** | encja główna z `@Version` (blokada optymistyczna); jedno repozytorium na agregat, zapis całości w jednej transakcji |
| **warianty** | `sealed interface` + `record`-y; w JSON `@JsonTypeInfo`/`@JsonSubTypes`, w bazie kolumna typu |
| **wynik operacji** | wynik zwracany z serwisu aplikacyjnego, kontroler mapuje warianty na status HTTP i `ProblemDetail` |
| **zdarzenie** | `record` publikowany przez `ApplicationEventPublisher` lub `AbstractAggregateRoot.registerEvent`; odbiór `@TransactionalEventListener` / `@ApplicationModuleListener` |
| **polityka** | bean (interfejs + implementacja) wstrzykiwany do serwisu aplikacyjnego lub fabryki agregatu |
| **repozytorium** | port w domenie, adapter jako interfejs Spring Data (`JpaRepository`/`ListCrudRepository`) w infrastrukturze |
| **read model** | projekcja Spring Data (interfejs lub `record`), `JdbcClient` z SQL, osobny endpoint zapytań |
| **maszyna stanów** | stan jako `sealed interface` lub `enum` w agregacie, przejścia w metodach domeny; Spring Statemachine tylko przy złożonych, konfigurowalnych przepływach |
| **moduł** | pakiet najwyższego poziomu pod klasą `@SpringBootApplication`; granice pilnuje Spring Modulith (`verify()`) lub ArchUnit |

## Źródła
Dostęp 2026-10-18; docs.spring.io niedostępne z sesji, więc dokumentacja czytana z repozytorium (gałąź 4.1.x).
- Spring Boot 4.0 Migration Guide — https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
- Dokumentacja Spring Boot 4.1.x (testing, testcontainers, actuator, web/servlet, io/rest-client, system-requirements) —
  https://github.com/spring-projects/spring-boot/tree/4.1.x/documentation/spring-boot-docs
- Wersje: Maven Central (spring-boot 4.1.1 i 3.5.16, testcontainers 2.0.5, junit-jupiter 6.1.3, spring-security 7.1.1,
  spring-modulith 2.1.1); https://spring.io/projects/spring-boot
- Daty wsparcia [wtórne]: endoflife.date (repozytorium GitHub, plik products/spring-boot.md).
- Testcontainers 2.0 release notes — https://github.com/testcontainers/testcontainers-java/releases/tag/2.0.0
Opisane własnymi słowami.
