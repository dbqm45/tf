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
# 0003. Hosting: App Service (Linux) + PostgreSQL Flexible Server in one EU region

## Context
Azure hosting, data in the EU, 99.5% availability only during 7:00–19:00 (not 24/7), a low operations budget, one back-end
developer without confirmed experience with containers. Poland Central (Warsaw) and West Europe (the Netherlands) are EU regions;
Poland Central has 3 availability zones, but the availability of App Service/Container Apps in this region has not been confirmed in a primary source.

## Decision
- Compute: **Azure App Service, Linux, Java SE 25 (Microsoft Build of OpenJDK), Premium v3 plan**, 1 instance in the MVP, a deployment slot for zero-downtime deployments.
- Database: **Azure Database for PostgreSQL Flexible Server 18, General Purpose** (not Burstable — only GP/MO allows turning on HA later), HA off in the MVP (SLA 99.9%).
- Secrets: Key Vault + Managed Identity; Entra ID sign-in to the database (Managed Identity), no passwords in the configuration.
- Telemetry: Application Insights / Log Analytics in **the same region**.
- Region: **Poland Central, if spike S0 confirms the availability of App Service and PostgreSQL Flexible GP**; otherwise another EU region with availability zones (Germany West Central or West Europe) — **[proposal]**, the final choice after the user's answer about the company's location and a "data in the country" requirement.

## Options considered
- App Service (chosen) — pros: a JAR deployment without Docker, the Java runtime patched by Azure, slots, the fewest parts; cons: less portability than a container (softened by the fact that the application is an ordinary Spring Boot JAR).
- Container Apps — pros: containers (portability), scaling to zero; cons: images, a registry, an ACA environment to maintain; unconfirmed availability in Poland Central.
- AKS — rejected for the MVP: the operational cost of a cluster is disproportionate to 300 users and 1 back-end developer.
- Database HA from the start (zonal 99.95% / zone-redundant 99.99%) — not now: the 99.5% requirement during working hours is met by the configuration without HA; the database cost roughly doubles.

## Consequences
- One region = no resilience to a failure of the whole region (accepted with 99.5% during 7:00–19:00). Backups in the same EU region.
- Deployments outside 7:00–19:00 or by a slot swap.
- Reversibility: database HA and a second App Service instance can be turned on without a migration; moving to Container Apps = adding a Dockerfile.
- To do: spike S0 (availability of the services and SKUs in the region), Terraform for the whole environment, an availability alert (Application Insights availability test) during 7:00–19:00.
