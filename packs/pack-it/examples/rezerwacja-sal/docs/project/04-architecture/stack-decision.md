---
artifact: stack-decision
phase: architecture
status: accepted
version: 1
author: tomasz-solution-architect
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/01-discovery/brief.md, docs/project/03-requirements/requirements.md]
---
# Decyzja o stacku: Rezerwacja sal i biurek (MVP)

## TL;DR
Modularny monolit: **Java 25 + Spring Boot 4.1 + Spring Modulith 2.x** (backend) i **Angular 22 + MSAL Angular** (front, serwowany z tej samej aplikacji), baza **Azure Database for PostgreSQL Flexible Server 18**, hosting **Azure App Service (Linux)** w jednym regionie UE, integracja z M365 przez **Microsoft Graph** (outbox, synchronizacja w jedną stronę).
Dlaczego: (1) scenariusz „0 podwójnych rezerwacji” gwarantuje baza — **exclusion constraint** na (zasób, przedział czasu), niezależnie od kodu; (2) stack, który zespół zna (TS/Angular + Java/Spring), z najmniejszą liczbą elementów do utrzymania; (3) nowy typ zasobu = dane + polityka w module Zasoby, bez zmian schematu rezerwacji.
Największe ryzyka: źródło prawdy dla sal, jeśli sale są już skrzynkami zasobów w Exchange (pytanie do IT), uprawnienia Graph (zgoda administratora M365), dostępność usług w regionie Poland Central, jeden programista Javy. Sprawdzamy spike'ami S0–S4 w pierwszych 2 tygodniach.
Uwaga: brak fazy domeny (02-domain) — model „Availability” przyjęty jako **[propozycja]** na podstawie historyjek H1–H4.

## Czynniki decyzyjne (drivers)
| Czynnik | Źródło (wymaganie/ograniczenie) | Waga (1–5) |
|---|---|---|
| Spójność: 50 równoczesnych prób → dokładnie 1 sukces, 0 podwójnych rezerwacji | requirements: Atrybuty jakości (H,H) | 5 |
| MVP w 3 miesiące, zespół 2 × TS/Angular + 1 × Java (Spring) | brief: Ograniczenia | 5 |
| Modyfikowalność: nowy typ zasobu w ≤ 2 dni | requirements (H,M) | 4 |
| Bezpieczeństwo: tylko Entra ID, dane w UE | requirements (H,M), brief | 4 |
| Niski koszt utrzymania | brief: Ograniczenia | 4 |
| Dostępność 99,5% w godz. 7–19 (nie 24/7) | requirements (M,M) | 2 |

## Filtry obowiązkowe
- Hosting Azure, wszystkie dane (baza, logi, kopie, sekrety) w regionie UE.
- Wsparcie (LTS/OSS) co najmniej do końca MVP + plan aktualizacji po MVP.
- Start bez nauki nowego języka: TypeScript i Java.
- Uwierzytelnianie wyłącznie Entra ID (OIDC), bez lokalnych kont.
- Licencje bez opłat: Oracle JDK 21 od aktualizacji z X 2026 przechodzi na licencję OTN — dlatego **OpenJDK (Microsoft Build) 25**, nie Oracle JDK.
- Odpadło po filtrach: Cosmos DB/NoSQL (brak ograniczeń na nakładające się przedziały), mikroserwisy (patrz ADR-0001).

## Rozważane opcje
| Obszar | Opcja A (domyślna, „nudna”) | Opcja B | Opcja C |
|---|---|---|---|
| Styl architektury | modularny monolit | mikroserwisy | serverless (Functions) |
| Backend | Java 25 + Spring Boot 4.1 | TypeScript + NestJS | — |
| Kontrola współbieżności | PostgreSQL exclusion constraint | `SELECT … FOR UPDATE` na zasobie | optimistic locking (`@Version`) / unikalny slot |
| Compute | App Service (Linux, Java SE) | Container Apps | AKS |
| Uwierzytelnianie w SPA | MSAL Angular (auth code + PKCE) + API jako resource server | BFF (sesja po stronie Springa) | — |
| Integracja M365 | Graph, uprawnienia aplikacyjne + outbox | Graph delegowany (OBO), synchronicznie | zaproszenie .ics mailem |

## Macierz oceny
Skala 1–5, w nawiasie waga. Szczegóły współbieżności: ADR-0002, compute i region: ADR-0003, M365: ADR-0004.

**Backend**
| Kryterium (waga) | A: Spring Boot | B: NestJS |
|---|---|---|
| dopasowanie do czynników (5) | 5 | 4 |
| kompetencje zespołu (4) | 3 (1 osoba) | 4 (3 osoby znają TS, brak doświadczenia z backendem Nest — do potwierdzenia) |
| dojrzałość ekosystemu (3) | 5 | 4 |
| koszt operacyjny i złożoność (4) | 3 (dwa języki) | 4 (jeden język) |
| przyjazność dla agentów AI (2) | 4 (lang-java) | 4 (lang-typescript) |
| uzależnienie / koszt wyjścia (2) | 4 | 4 |
| bezpieczeństwo (3) | 5 (Spring Security) | 4 |
| **Suma ważona** | **95** | **92** |

Wynik jest bliski. O wyborze A decyduje ograniczenie z briefu (zespół: Java/Spring na backendzie) oraz dojrzałość Spring Security i Spring Modulith (granice modułów + outbox z pudełka). Ryzyko „1 programista Javy” — w sekcji Ryzyka.

**Compute**
| Kryterium (waga) | App Service | Container Apps | AKS |
|---|---|---|---|
| dopasowanie (5) | 5 | 5 | 4 |
| kompetencje (4) | 5 (wdrożenie JAR) | 3 (obrazy kontenerów) | 1 |
| dojrzałość (3) | 5 | 4 | 5 |
| koszt i złożoność (4) | 4 | 4 | 1 |
| AI (2) | 4 | 4 | 3 |
| koszt wyjścia (2) | 3 | 4 | 5 |
| bezpieczeństwo (3) | 4 (runtime łatany przez Azure) | 4 | 3 |
| **Suma** | **102** | **93** | **68** |

**Współbieżność**
| Kryterium (waga) | Exclusion constraint | `FOR UPDATE` | Optimistic / unikalny slot |
|---|---|---|---|
| gwarancja 0 podwójnych niezależnie od ścieżki kodu (5) | 5 | 3 | 3 / 5 |
| prostota (4) | 4 | 4 | 3 / 3 |
| dowolne przedziały + blokady serwisowe w jednym mechanizmie (4) | 5 | 5 | 4 / 2 |
| przenośność między bazami (2) | 2 | 5 | 5 / 5 |
| **Suma** | **65** | **61** | **53 / 55** |

## Fakty zweryfikowane (wersje, wsparcie, licencje — ze źródłami i datą)
| Technologia | Wersja / LTS / koniec wsparcia | Źródło | Sprawdzono |
|---|---|---|---|
| Java | 25 LTS (IX 2025), premier support do IX 2030; JDK 21 Oracle od X 2026 na licencji OTN | [Oracle Java SE Support Roadmap](https://www.oracle.com/java/technologies/java-se-support-roadmap.html) | 2026-09-27 |
| Microsoft Build of OpenJDK | 25 wspierane na App Service i Container Apps, łatki kwartalne | [MS OpenJDK support](https://learn.microsoft.com/en-us/java/openjdk/support), [App Service runtime policy](https://learn.microsoft.com/en-us/azure/app-service/language-support-policy) | 2026-09-27 |
| Spring Boot | 4.1.x (4.1.1 VIII 2026), OSS do 2027-07-31; 4.0 OSS do 2026-12-31; baseline Java 17 | [endoflife.date/spring-boot](https://endoflife.date/spring-boot), [spring.io](https://spring.io/blog/2025/11/20/spring-boot-4-0-0-available-now/) | 2026-09-27 |
| Spring Modulith | 2.x (2.0 GA XI 2025, baseline Boot 4), Event Publication Registry (JDBC) | [spring.io blog](https://spring.io/blog/2025/11/21/spring-modulith-2-0-ga-1-4-5-and-1-3-11-released/) | 2026-09-27 |
| Angular | 22.2.0 (22 wydany 2026-06-03, aktywne wsparcie 6 mies. + 12 mies. LTS); wymaga TypeScript `>=6.0 <6.1` | [angular.dev/reference/releases](https://angular.dev/reference/releases), `npm view @angular/compiler-cli@22 peerDependencies` | 2026-09-27 |
| MSAL Angular | `@azure/msal-angular` 6.2.1, peer: `@azure/msal-browser ^5.22.0`, `rxjs ^7.4.0` (brak jawnego zakresu Angulara → spike S4) | `npm view @azure/msal-angular` | 2026-09-27 |
| PostgreSQL (Azure Flexible Server) | wersje 11–18, 18 GA; `btree_gist` dostępne (wymaga dodania do `azure.extensions`) | [Supported versions](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-supported-versions), [Extensions](https://learn.microsoft.com/en-us/azure/postgresql/extensions/concepts-extensions-versions) | 2026-09-27 |
| SLA PostgreSQL Flexible | bez HA 99,9%, HA strefowe 99,95%, HA międzystrefowe 99,99% (HA niedostępne w warstwie Burstable) | [HA concepts](https://learn.microsoft.com/en-us/azure/postgresql/high-availability/concepts-high-availability) | 2026-09-27 |
| Region Poland Central | GA, Warszawa, 3 strefy dostępności, w UE; **dostępność App Service/Container Apps w regionie niepotwierdzona w źródle pierwotnym** → spike S0 | [Azure geographies](https://azure.microsoft.com/en-us/explore/global-infrastructure/geographies), [Products by region](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region) | 2026-09-27 |
| Exchange Online RBAC for Applications | zastępuje Application Access Policies; zawęża `Calendars.ReadWrite` (app) do zakresu skrzynek | [Application RBAC](https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac) | 2026-09-27 |

## Rekomendacja
| Warstwa | Wybór | Uzasadnienie |
|---|---|---|
| Styl | modularny monolit, jedna jednostka wdrożenia (ADR-0001) | 1 zespół, 3 mies.; moduły: `resources`, `booking` (Availability), `calendarsync`, `identity` |
| Backend | Java 25 (Microsoft Build of OpenJDK), Spring Boot 4.1, Spring Modulith 2.x, Spring Data JPA/JDBC, Flyway, Maven | znane zespołowi; Modulith = testy granic modułów + outbox |
| Współbieżność | PostgreSQL 18: tabela alokacji z `tstzrange` + `EXCLUDE USING gist (resource_id WITH =, period WITH &&) WHERE (aktywne)` (ADR-0002) | gwarancja w bazie; rezerwacje i blokady serwisowe w jednym mechanizmie; błąd `23P01` → czytelna odmowa |
| No-show (H4) | zadanie `@Scheduled` co 1 min: jeden idempotentny `UPDATE … RETURNING` | bez dodatkowego schedulera i blokad rozproszonych |
| Frontend | Angular 22 (TS 6.0), standalone + signals, budowany w CI i serwowany jako statyczne zasoby przez Spring Boot **[propozycja]** | jedno źródło (brak CORS), jedna usługa do utrzymania |
| Auth | Entra ID: MSAL Angular (auth code + PKCE) → token do API; backend `spring-boot-starter-oauth2-resource-server` (walidacja JWT, app roles `Employee`, `Facility`) | standard Microsoft, bezstanowy backend; BFF jako ścieżka wzmocnienia, gdy wymagać tego będzie przegląd bezpieczeństwa |
| M365 | Microsoft Graph SDK (Java), uprawnienia aplikacyjne zawężone przez Exchange RBAC for Applications, wysyłka z outboxa (ADR-0004) | awaria Graph nie blokuje rezerwacji; ponowienia |
| Hosting | App Service Linux (Premium v3), PostgreSQL Flexible General Purpose (najmniejszy rozmiar, HA wyłączone w MVP), Key Vault, Managed Identity (także do bazy — bez haseł), Application Insights (OpenTelemetry) — wszystko w jednym regionie UE (ADR-0003) | 99,5% w godz. 7–19 osiągalne w jednym regionie; HA bazy włączalne później bez migracji |
| Region | Poland Central, jeśli S0 potwierdzi dostępność usług; w przeciwnym razie inny region UE ze strefami (np. Germany West Central / West Europe) | wszystkie w UE; wybór ostateczny po S0 i odpowiedzi użytkownika |
| IaC / CI | Terraform (azurerm), pipeline GitHub Actions **[propozycja — zależy od tego, gdzie jest repo]** | skille ops-iac-terraform, ops-ci-cd dostępne |
| Testy | JUnit + Testcontainers (PostgreSQL 18), test Modulith `verify()`, testy Angulara wg domyślnego runnera CLI | fitness functions poniżej |

**Fitness functions (w CI):** (1) test współbieżności: 50 równoległych rezerwacji tej samej sali → dokładnie 1 sukces, 49 odmów z kodem `RESOURCE_UNAVAILABLE`; (2) `ApplicationModules.verify()` — brak naruszeń granic modułów; (3) skan zależności (OWASP/Dependabot); (4) test akceptacyjny „nowy typ zasobu” dodany wyłącznie migracją danych + konfiguracją polityki.

**Modyfikowalność (≤ 2 dni):** typ zasobu to dane (`resource_type`: jednostka rezerwacji PRZEDZIAŁ/DZIEŃ, wymagane potwierdzenie obecności, maks. długość) + opcjonalna klasa polityki. Moduł `booking` nie zna typów — operuje na (zasób, przedział). Rezerwacja biurka na dzień = przedział [początek dnia, koniec dnia) w tej samej tabeli.

## Ryzyka i eksperymenty (spike)
| Ryzyko | Jak sprawdzimy | Kryterium porzucenia wyboru |
|---|---|---|
| S0: App Service Linux / PostgreSQL Flexible GP niedostępne w Poland Central dla subskrypcji | `az provider show -n Microsoft.Web` / `az postgres flexible-server list-skus -l polandcentral`, próbne utworzenie zasobów (0,5 dnia) | brak którejkolwiek usługi → region zapasowy UE |
| S1: exclusion constraint + JPA — mapowanie błędu `23P01`, zachowanie przy 50 równoległych żądaniach | prototyp + test Testcontainers (1 dzień) | > 1 sukces lub zakleszczenia/timeouty p95 > 1 s → wariant `FOR UPDATE` na zasobie (ADR-0002, opcja B) |
| S2: Sale już są skrzynkami zasobów w Exchange → dwa źródła prawdy, podwójne rezerwacje „z Outlooka” | pytanie do IT + test na tenancie deweloperskim (1 dzień) | nie da się zablokować bezpośrednich rezerwacji w Exchange → decyzja użytkownika o źródle prawdy (nowa wersja ADR-0004) |
| S3: zgoda administratora M365 na `Calendars.ReadWrite` (app) zawężone RBAC | uzgodnienie z IT + zapis wydarzenia do testowej skrzynki (1–2 dni) | brak zgody → opcja C z ADR-0004 (zaproszenie .ics) |
| S4: zgodność MSAL Angular 6.x z Angular 22 (brak jawnego peer dependency) | szkielet aplikacji, logowanie + wywołanie API (0,5 dnia) | błędy runtime/build bez obejścia → BFF (Spring `oauth2Login`, sesja) |
| 1 programista Javy (bus factor, wąskie gardło) | plan: backend mały (6 historyjek), front-endowcy piszą testy API i kod modułu `calendarsync` w parach | opóźnienie backendu > 2 tyg. po pierwszej iteracji → rozważyć NestJS przed dalszym rozwojem (koszt: przepisanie modułów) |
| Spring Boot 4.1 OSS kończy się 2027-07-31 | aktualizacje minor co pół roku w backlogu po MVP | — |

## Skille i persony
- Potrzebne skille — dostępne: `lang-java`, `lang-typescript`, `fw-angular`, `be-database`, `be-api-design`, `be-auth-security`, `ops-iac-terraform`, `ops-ci-cd`, `ops-observability`, `eng-testing`, `ddd-archetypes` (Availability). Do utworzenia: `fw-spring-boot` (Spring Boot 4.x, Spring Modulith 2.x, Spring Security resource server), ewentualnie `integ-microsoft-graph`.
- Sugerowany `stack` person: backend `[lang-java, fw-spring-boot, be-database, be-api-design, be-auth-security]`, frontend `[fw-angular, lang-typescript, fe-architecture]`, ops `[ops-iac-terraform, ops-ci-cd, ops-observability]`.

## Otwarte pytania
- [ ] Czy sale są dziś skrzynkami zasobów (room mailbox) w Exchange i czy pracownicy rezerwują je bezpośrednio w Outlooku? Kto ma być źródłem prawdy? → IT / właściciel produktu
- [ ] Czy administrator M365 udzieli zgody na uprawnienie aplikacyjne `Calendars.ReadWrite` zawężone do grupy pracowników i sal? → IT
- [ ] Gdzie fizycznie jest firma (wybór regionu: Poland Central vs inny region UE) i czy jest wymóg danych „w kraju”, czy wystarczy UE? → użytkownik
- [ ] Jak pracownik potwierdza obecność (H4): przycisk w aplikacji, kod QR przy biurku/sali, inne? → facility / właściciel produktu
- [ ] Budżet miesięczny na Azure (warunkuje HA bazy i drugą instancję App Service) → użytkownik
- [ ] Gdzie jest repozytorium i CI (GitHub vs Azure DevOps)? → IT
- [ ] Czy programiści TS mogą/chcą pracować w backendzie Java (ryzyko 1 osoby)? → użytkownik

## Przekazanie
- **Dla:** użytkownik (akceptacja), potem orkiestrator planu i persony wykonawcze backend/frontend
- **Zadanie:** użytkownik — akceptacja rekomendacji i odpowiedzi na Otwarte pytania (zwłaszcza źródło prawdy dla sal i zgoda M365) przed startem implementacji; orkiestrator — plan 05-plan/plan.md, w którym spike'i S0–S4 są w pierwszej iteracji, a pierwszym cięciem pionowym jest H6 + H1 bez synchronizacji M365
- **Przeczytaj:** TL;DR, Rekomendacja, Ryzyka i eksperymenty, ADR-0001 do ADR-0004
- **Nie rób:** nie zaczynaj integracji Graph przed odpowiedzią IT (S2, S3); nie dodawaj osobnych serwisów ani kolejek (Service Bus) — outbox Modulith wystarcza; nie używaj Oracle JDK
- **Gotowe, gdy:** status accepted (po zgodzie użytkownika), a spike'i S0–S4 mają wynik zapisany w 06-delivery
