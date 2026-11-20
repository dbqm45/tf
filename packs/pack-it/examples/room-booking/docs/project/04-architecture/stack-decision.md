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
# Stack decision: Room and desk booking (MVP)

## TL;DR
A modular monolith: **Java 25 + Spring Boot 4.1 + Spring Modulith 2.x** (back end) and **Angular 22 + MSAL Angular** (front end, served by the same application), database **Azure Database for PostgreSQL Flexible Server 18**, hosting **Azure App Service (Linux)** in one EU region, M365 integration through **Microsoft Graph** (outbox, one-way synchronisation).
Why: (1) the database guarantees the "0 double bookings" scenario — an **exclusion constraint** on (resource, time slot), regardless of the code; (2) a stack the team knows (TS/Angular + Java/Spring), with the fewest parts to maintain; (3) a new resource type = data + a policy in the Resources module, without changes to the booking schema.
The biggest risks: the source of truth for rooms, if the rooms are already resource mailboxes in Exchange (a question for IT), Graph permissions (the M365 administrator's consent), the availability of the services in the Poland Central region, one Java developer. We check them with spikes S0–S4 in the first 2 weeks.
Note: no domain phase (02-domain) — the "Availability" model is adopted as a **[proposal]** based on stories H1–H4.

## Decision drivers
| Driver | Source (requirement/constraint) | Weight (1–5) |
|---|---|---|
| Consistency: 50 simultaneous attempts → exactly 1 success, 0 double bookings | requirements: Quality attributes (H,H) | 5 |
| MVP in 3 months, a team of 2 × TS/Angular + 1 × Java (Spring) | brief: Constraints | 5 |
| Modifiability: a new resource type in ≤ 2 days | requirements (H,M) | 4 |
| Security: only Entra ID, data in the EU | requirements (H,M), brief | 4 |
| Low operations cost | brief: Constraints | 4 |
| 99.5% availability during 7:00–19:00 (not 24/7) | requirements (M,M) | 2 |

## Mandatory filters
- Azure hosting, all data (database, logs, backups, secrets) in an EU region.
- Support (LTS/OSS) at least until the end of the MVP + an upgrade plan after the MVP.
- A start without learning a new language: TypeScript and Java.
- Authentication only through Entra ID (OIDC), no local accounts.
- Licences without fees: Oracle JDK 21 moves to the OTN licence from the October 2026 update — hence **OpenJDK (Microsoft Build) 25**, not Oracle JDK.
- Dropped by the filters: Cosmos DB/NoSQL (no constraints on overlapping ranges), microservices (see ADR-0001).

## Options considered
| Area | Option A (default, "boring") | Option B | Option C |
|---|---|---|---|
| Architecture style | modular monolith | microservices | serverless (Functions) |
| Back end | Java 25 + Spring Boot 4.1 | TypeScript + NestJS | — |
| Concurrency control | PostgreSQL exclusion constraint | `SELECT … FOR UPDATE` on the resource | optimistic locking (`@Version`) / a unique slot |
| Compute | App Service (Linux, Java SE) | Container Apps | AKS |
| Authentication in the SPA | MSAL Angular (auth code + PKCE) + the API as a resource server | BFF (a session on the Spring side) | — |
| M365 integration | Graph, application permissions + outbox | delegated Graph (OBO), synchronously | an .ics invitation by email |

## Assessment matrix
Scale 1–5, the weight in brackets. Concurrency details: ADR-0002, compute and region: ADR-0003, M365: ADR-0004.

**Back end**
| Criterion (weight) | A: Spring Boot | B: NestJS |
|---|---|---|
| fit to the drivers (5) | 5 | 4 |
| team skills (4) | 3 (1 person) | 4 (3 people know TS, no experience with a Nest back end — to be confirmed) |
| ecosystem maturity (3) | 5 | 4 |
| operational cost and complexity (4) | 3 (two languages) | 4 (one language) |
| friendliness for AI agents (2) | 4 (lang-java) | 4 (lang-typescript) |
| lock-in / exit cost (2) | 4 | 4 |
| security (3) | 5 (Spring Security) | 4 |
| **Weighted sum** | **95** | **92** |

The result is close. The choice of A is decided by the constraint from the brief (the team: Java/Spring on the back end) and the maturity of Spring Security and Spring Modulith (module boundaries + an outbox out of the box). The "1 Java developer" risk — in the Risks section.

**Compute**
| Criterion (weight) | App Service | Container Apps | AKS |
|---|---|---|---|
| fit (5) | 5 | 5 | 4 |
| skills (4) | 5 (JAR deployment) | 3 (container images) | 1 |
| maturity (3) | 5 | 4 | 5 |
| cost and complexity (4) | 4 | 4 | 1 |
| AI (2) | 4 | 4 | 3 |
| exit cost (2) | 3 | 4 | 5 |
| security (3) | 4 (runtime patched by Azure) | 4 | 3 |
| **Sum** | **102** | **93** | **68** |

**Concurrency**
| Criterion (weight) | Exclusion constraint | `FOR UPDATE` | Optimistic / unique slot |
|---|---|---|---|
| a guarantee of 0 double bookings regardless of the code path (5) | 5 | 3 | 3 / 5 |
| simplicity (4) | 4 | 4 | 3 / 3 |
| any slots + maintenance blocks in one mechanism (4) | 5 | 5 | 4 / 2 |
| portability between databases (2) | 2 | 5 | 5 / 5 |
| **Sum** | **65** | **61** | **53 / 55** |

## Verified facts (versions, support, licences — with sources and a date)
| Technology | Version / LTS / end of support | Source | Checked |
|---|---|---|---|
| Java | 25 LTS (September 2025), premier support until September 2030; Oracle JDK 21 on the OTN licence from October 2026 | [Oracle Java SE Support Roadmap](https://www.oracle.com/java/technologies/java-se-support-roadmap.html) | 2026-09-27 |
| Microsoft Build of OpenJDK | 25 supported on App Service and Container Apps, quarterly patches | [MS OpenJDK support](https://learn.microsoft.com/en-us/java/openjdk/support), [App Service runtime policy](https://learn.microsoft.com/en-us/azure/app-service/language-support-policy) | 2026-09-27 |
| Spring Boot | 4.1.x (4.1.1 August 2026), OSS until 2027-07-31; 4.0 OSS until 2026-12-31; Java 17 baseline | [endoflife.date/spring-boot](https://endoflife.date/spring-boot), [spring.io](https://spring.io/blog/2025/11/20/spring-boot-4-0-0-available-now/) | 2026-09-27 |
| Spring Modulith | 2.x (2.0 GA November 2025, Boot 4 baseline), Event Publication Registry (JDBC) | [spring.io blog](https://spring.io/blog/2025/11/21/spring-modulith-2-0-ga-1-4-5-and-1-3-11-released/) | 2026-09-27 |
| Angular | 22.2.0 (22 released 2026-06-03, active support 6 months + 12 months LTS); requires TypeScript `>=6.0 <6.1` | [angular.dev/reference/releases](https://angular.dev/reference/releases), `npm view @angular/compiler-cli@22 peerDependencies` | 2026-09-27 |
| MSAL Angular | `@azure/msal-angular` 6.2.1, peer: `@azure/msal-browser ^5.22.0`, `rxjs ^7.4.0` (no explicit Angular range → spike S4) | `npm view @azure/msal-angular` | 2026-09-27 |
| PostgreSQL (Azure Flexible Server) | versions 11–18, 18 GA; `btree_gist` available (must be added to `azure.extensions`) | [Supported versions](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-supported-versions), [Extensions](https://learn.microsoft.com/en-us/azure/postgresql/extensions/concepts-extensions-versions) | 2026-09-27 |
| PostgreSQL Flexible SLA | without HA 99.9%, zonal HA 99.95%, zone-redundant HA 99.99% (HA not available in the Burstable tier) | [HA concepts](https://learn.microsoft.com/en-us/azure/postgresql/high-availability/concepts-high-availability) | 2026-09-27 |
| Poland Central region | GA, Warsaw, 3 availability zones, in the EU; **the availability of App Service/Container Apps in the region not confirmed in a primary source** → spike S0 | [Azure geographies](https://azure.microsoft.com/en-us/explore/global-infrastructure/geographies), [Products by region](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region) | 2026-09-27 |
| Exchange Online RBAC for Applications | replaces Application Access Policies; narrows `Calendars.ReadWrite` (app) to a scope of mailboxes | [Application RBAC](https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac) | 2026-09-27 |

## Recommendation
| Layer | Choice | Rationale |
|---|---|---|
| Style | a modular monolith, one deployment unit (ADR-0001) | 1 team, 3 months; modules: `resources`, `booking` (Availability), `calendarsync`, `identity` |
| Back end | Java 25 (Microsoft Build of OpenJDK), Spring Boot 4.1, Spring Modulith 2.x, Spring Data JPA/JDBC, Flyway, Maven | known to the team; Modulith = module boundary tests + an outbox |
| Concurrency | PostgreSQL 18: an allocation table with `tstzrange` + `EXCLUDE USING gist (resource_id WITH =, period WITH &&) WHERE (active)` (ADR-0002) | a guarantee in the database; bookings and maintenance blocks in one mechanism; the `23P01` error → a clear refusal |
| No-show (H4) | a `@Scheduled` job every 1 min: one idempotent `UPDATE … RETURNING` | no extra scheduler and no distributed locks |
| Front end | Angular 22 (TS 6.0), standalone + signals, built in CI and served as static assets by Spring Boot **[proposal]** | one origin (no CORS), one service to maintain |
| Auth | Entra ID: MSAL Angular (auth code + PKCE) → a token to the API; back end `spring-boot-starter-oauth2-resource-server` (JWT validation, app roles `Employee`, `Facility`) | the Microsoft standard, a stateless back end; BFF as a hardening path when a security review requires it |
| M365 | Microsoft Graph SDK (Java), application permissions narrowed by Exchange RBAC for Applications, sending from the outbox (ADR-0004) | a Graph failure does not block the booking; retries |
| Hosting | App Service Linux (Premium v3), PostgreSQL Flexible General Purpose (the smallest size, HA off in the MVP), Key Vault, Managed Identity (also for the database — no passwords), Application Insights (OpenTelemetry) — all in one EU region (ADR-0003) | 99.5% during 7:00–19:00 is achievable in one region; database HA can be turned on later without a migration |
| Region | Poland Central, if S0 confirms the availability of the services; otherwise another EU region with zones (e.g. Germany West Central / West Europe) | all in the EU; the final choice after S0 and the user's answer |
| IaC / CI | Terraform (azurerm), a GitHub Actions pipeline **[proposal — depends on where the repo is]** | skills ops-iac-terraform, ops-ci-cd available |
| Tests | JUnit + Testcontainers (PostgreSQL 18), the Modulith `verify()` test, Angular tests with the CLI's default runner | fitness functions below |

**Fitness functions (in CI):** (1) a concurrency test: 50 parallel bookings of the same room → exactly 1 success, 49 refusals with the code `RESOURCE_UNAVAILABLE`; (2) `ApplicationModules.verify()` — no module boundary violations; (3) a dependency scan (OWASP/Dependabot); (4) an acceptance test "a new resource type" added only by a data migration + a policy configuration.

**Modifiability (≤ 2 days):** a resource type is data (`resource_type`: the booking unit SLOT/DAY, a check-in required, a maximum length) + an optional policy class. The `booking` module does not know the types — it operates on (resource, slot). Booking a desk for a day = the slot [start of the day, end of the day) in the same table.

## Risks and experiments (spikes)
| Risk | How we check it | Criterion for dropping the choice |
|---|---|---|
| S0: App Service Linux / PostgreSQL Flexible GP not available in Poland Central for the subscription | `az provider show -n Microsoft.Web` / `az postgres flexible-server list-skus -l polandcentral`, a trial creation of the resources (0.5 day) | any service missing → a fallback EU region |
| S1: exclusion constraint + JPA — mapping the `23P01` error, behaviour with 50 parallel requests | a prototype + a Testcontainers test (1 day) | > 1 success or deadlocks/timeouts p95 > 1 s → the `FOR UPDATE` on the resource variant (ADR-0002, option B) |
| S2: The rooms are already resource mailboxes in Exchange → two sources of truth, double bookings "from Outlook" | a question for IT + a test on a developer tenant (1 day) | direct bookings in Exchange cannot be blocked → the user's decision about the source of truth (a new version of ADR-0004) |
| S3: the M365 administrator's consent to `Calendars.ReadWrite` (app) narrowed by RBAC | agreement with IT + writing an event to a test mailbox (1–2 days) | no consent → option C from ADR-0004 (an .ics invitation) |
| S4: compatibility of MSAL Angular 6.x with Angular 22 (no explicit peer dependency) | an application skeleton, sign-in + an API call (0.5 day) | runtime/build errors without a workaround → BFF (Spring `oauth2Login`, a session) |
| 1 Java developer (bus factor, a bottleneck) | plan: a small back end (6 stories), the front-end developers write API tests and the code of the `calendarsync` module in pairs | a back-end delay > 2 weeks after the first iteration → consider NestJS before further development (cost: rewriting the modules) |
| Spring Boot 4.1 OSS ends on 2027-07-31 | minor upgrades every half year in the backlog after the MVP | — |

## Skills and personas
- Skills needed — available: `lang-java`, `lang-typescript`, `fw-angular`, `be-database`, `be-api-design`, `be-auth-security`, `ops-iac-terraform`, `ops-ci-cd`, `ops-observability`, `eng-testing`, `ddd-archetypes` (Availability). To create: `fw-spring-boot` (Spring Boot 4.x, Spring Modulith 2.x, Spring Security resource server), possibly `integ-microsoft-graph`.
- Suggested `stack` of the personas: back end `[lang-java, fw-spring-boot, be-database, be-api-design, be-auth-security]`, front end `[fw-angular, lang-typescript, fe-architecture]`, ops `[ops-iac-terraform, ops-ci-cd, ops-observability]`.

## Open questions
- [ ] Are the rooms resource mailboxes (room mailbox) in Exchange today, and do employees book them directly in Outlook? Who is to be the source of truth? → IT / product owner
- [ ] Will the M365 administrator consent to the application permission `Calendars.ReadWrite` narrowed to the group of employees and rooms? → IT
- [ ] Where is the company physically (the region choice: Poland Central vs another EU region), and is there a "data in the country" requirement, or is the EU enough? → user
- [ ] How does an employee check in (H4): a button in the application, a QR code at the desk/room, something else? → facility / product owner
- [ ] The monthly Azure budget (it determines database HA and a second App Service instance) → user
- [ ] Where are the repository and CI (GitHub vs Azure DevOps)? → IT
- [ ] Can/do the TS developers want to work on the Java back end (the 1-person risk)? → user

## Handoff
- **For:** user (acceptance), then the plan orchestrator and the back-end/front-end delivery personas
- **Task:** user — accept the recommendation and answer the Open questions (especially the source of truth for rooms and the M365 consent) before the implementation starts; orchestrator — the plan 05-plan/plan.md, in which spikes S0–S4 are in the first iteration and the first vertical slice is H6 + H1 without M365 synchronisation
- **Read:** TL;DR, Recommendation, Risks and experiments, ADR-0001 to ADR-0004
- **Do not:** do not start the Graph integration before IT's answer (S2, S3); do not add separate services or queues (Service Bus) — the Modulith outbox is enough; do not use Oracle JDK
- **Done when:** status accepted (after the user's consent), and spikes S0–S4 have their result recorded in 06-delivery
