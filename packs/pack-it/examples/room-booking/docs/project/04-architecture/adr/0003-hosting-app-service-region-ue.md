---
artifact: adr
phase: architecture
status: accepted
version: 1
author: tomasz-solution-architect
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md, docs/project/04-architecture/stack-decision.md]
---
# 0003. Hosting: App Service (Linux) + PostgreSQL Flexible Server w jednym regionie UE

## Kontekst
Hosting Azure, dane w UE, dostępność 99,5% tylko w godz. 7–19 (nie 24/7), niski budżet utrzymania, jeden programista
backendu bez potwierdzonego doświadczenia z kontenerami. Poland Central (Warszawa) i West Europe (Holandia) są regionami w UE;
Poland Central ma 3 strefy dostępności, ale dostępność App Service/Container Apps w tym regionie nie została potwierdzona w źródle pierwotnym.

## Decyzja
- Compute: **Azure App Service, Linux, Java SE 25 (Microsoft Build of OpenJDK), plan Premium v3**, 1 instancja w MVP, slot wdrożeniowy do wdrożeń bez przestoju.
- Baza: **Azure Database for PostgreSQL Flexible Server 18, General Purpose** (nie Burstable — tylko GP/MO pozwala włączyć HA później), HA wyłączone w MVP (SLA 99,9%).
- Sekrety: Key Vault + Managed Identity; do bazy logowanie Entra ID (Managed Identity), bez haseł w konfiguracji.
- Telemetria: Application Insights / Log Analytics w **tym samym regionie**.
- Region: **Poland Central, jeśli spike S0 potwierdzi dostępność App Service i PostgreSQL Flexible GP**; w przeciwnym razie inny region UE ze strefami dostępności (Germany West Central lub West Europe) — **[propozycja]**, ostateczny wybór po odpowiedzi użytkownika o lokalizacji firmy i wymogu „dane w kraju”.

## Rozważane opcje
- App Service (wybrana) — zalety: wdrożenie JAR bez Dockera, runtime Javy łatany przez Azure, sloty, najmniej elementów; wady: mniejsza przenośność niż kontener (łagodzi to fakt, że aplikacja to zwykły JAR Spring Boot).
- Container Apps — zalety: kontenery (przenośność), skalowanie do zera; wady: obrazy, rejestr, środowisko ACA do utrzymania; niepotwierdzona dostępność w Poland Central.
- AKS — odrzucone dla MVP: koszt operacyjny klastra nieproporcjonalny do 300 użytkowników i 1 programisty backendu.
- HA bazy od startu (zonal 99,95% / zone-redundant 99,99%) — nie teraz: wymóg 99,5% w godz. pracy spełnia konfiguracja bez HA; koszt bazy rośnie ok. dwukrotnie.

## Konsekwencje
- Jeden region = brak odporności na awarię całego regionu (akceptowane przy 99,5% w godz. 7–19). Kopie zapasowe w tym samym regionie UE.
- Wdrożenia poza godzinami 7–19 albo przez swap slotu.
- Odwracalność: HA bazy i druga instancja App Service włączalne bez migracji; przejście na Container Apps = dodanie Dockerfile.
- Do zrobienia: spike S0 (dostępność usług i SKU w regionie), Terraform dla całego środowiska, alert dostępności (Application Insights availability test) w godz. 7–19.
