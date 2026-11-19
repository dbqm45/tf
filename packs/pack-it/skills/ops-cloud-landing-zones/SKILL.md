---
name: ops-cloud-landing-zones
description: Use for designing a cloud foundation for many teams — landing zone, accounts and subscriptions, hub-spoke network, account vending.
metadata:
  review: "2027-04-17"
  visibility: name
  catalog: "Use when you design or put in order a cloud foundation for many teams (AWS, Azure, GCP) — what a landing zone is, the hierarchy of accounts, subscriptions and projects, and environments, identity federation and SSO, network topology (hub-and-spoke, transit gateway, Virtual WAN, Shared VPC), log and tooling accounts, preventive and detective guardrails, tagging and cost allocation, account vending and subscription vending in IaC, baseline configurations per workload type, versioning and evolving the landing zone. The result is a design document and a decision list. Not for the cloud security controls themselves (sec-cloud-security), Terraform modules, cost optimization (ops-finops), the developer platform (ops-platform-engineering) or moving workloads (ops-cloud-migration)."
  keywords: "wprowadzanie zmian w landing zone, zmiany dotykają wielu istniejących subskrypcji i kont, aktualizacja landing zone, nowa wersja landing zone, wersjonowanie fundamentu chmury, rollout zmian na wszystkie konta, zmiana fundamentu chmury, setki istniejących subskrypcji, setki kont, landing zone, zmiany w landing zone, wersjonowanie landing zone, aktualizacja landing zone, wdrażanie zmian na wiele subskrypcji, dryf kont, fundament chmury, cloud foundation, Control Tower, Landing Zone Accelerator, Azure landing zones, Cloud Adoption Framework, account vending, subscription vending, hierarchia kont, organizacja AWS, grupy zarządzania, foldery GCP, hub and spoke, transit gateway, Virtual WAN, Shared VPC, konto logów, guardrails, SCP, tagowanie, alokacja kosztów, nowe konto dla zespołu, wiele zespołów w chmurze, SSO chmura, introducing changes in a landing zone, changes touch many existing subscriptions and accounts, landing zone update, new landing zone version, cloud foundation versioning, rolling out changes to all accounts, cloud foundation change, hundreds of existing subscriptions, hundreds of accounts, changes in a landing zone, landing zone versioning, deploying changes to many subscriptions, account drift, account hierarchy, AWS organization, management groups, GCP folders, log account, tagging, cost allocation, new account for a team, many teams in the cloud, cloud SSO"
---

# Landing zone: a cloud foundation for many teams

A landing zone is a preconfigured, automated multi-account environment: the hierarchy, identity, network,
logging, guardrails and the process for creating new accounts. This skill describes **the structure and automation of the foundation**.
The content of security controls (encryption, CSPM, break-glass, benchmarks) is sec-cloud-security;
optimizing the bill is ops-finops. Result: `docs/project/04-architecture/landing-zone.md`
(core-project-record) with the design and a decision list (format below). You deploy nothing: changes in the cloud go as a plan
(`terraform plan`, audit mode, a change window) and go in after a human's approval.

## Procedure
1. **Scope and choice of pattern.** How many teams, clouds, regions, regulatory requirements, who maintains the foundation
   (the platform team: ops-platform-engineering). Choose a starting point, do not build from scratch:
   - AWS: **AWS Control Tower** (landing zone, controls, Account Factory); extensions: Account Factory for Terraform
     and **Landing Zone Accelerator on AWS**; a fully custom variant only for requirements these do not cover.
   - Azure: **Azure landing zones** in the Cloud Adoption Framework (platform landing zone + application landing zones,
     reference implementations in Bicep and Terraform).
   - GCP: **Google Cloud enterprise foundations blueprint** (formerly the security foundations blueprint) with Terraform.
   Product and blueprint names change; confirm in the vendor's documentation (core-source-research).
2. **Hierarchy and environments.** Organization → groups (OUs, management groups, folders) → accounts, subscriptions, projects.
   The account boundary is the boundary of permissions, limits and the bill, so **one workload × one environment = one account**
   (production separate from non-production). Groups by *policies*, not by the company org chart (reorganizations change
   the org chart, policies stay). A typical layout: `platform` (logs, security, network, identity, tools),
   `workloads` (prod, nonprod), `sandbox` (budget, auto-cleanup), `suspended`. The organization's management account
   without workloads. Minimal tree depth (depth limits: check with the vendor).
3. **Identity.** One source of truth (the company IdP) → SSO federation (AWS IAM Identity Center, Microsoft Entra ID,
   Cloud Identity / Workforce Identity Federation) → groups mapped to roles per account. Standard roles: platform
   admin, developer, read-only, audit. Local users in accounts forbidden by a guardrail. MFA, PAM
   and break-glass: sec-zero-trust-identity and sec-cloud-security; machine identities and OIDC in CI: ops-secrets-identities.
4. **Network.** An addressing plan (CIDR) with a registry **before** the first network is created: overlapping ranges block
   later interconnection, and a change is a migration. Topologies:
   - **hub-and-spoke**: a central hub with a firewall, DNS and the link to on-premises; workload networks as spokes. Implementation:
     AWS Transit Gateway, Azure Virtual WAN or a hub VNet, a GCP hub project with peering or NCC [unverified: current limits];
   - **Shared VPC** (GCP; in AWS the counterpart is VPC sharing through RAM): one network shared with workload
     projects/accounts, managed centrally;
   - **a network per workload** without a hub: simpler when there are few workloads and they connect little.
   Record: who owns the hub, centralized or distributed egress, name resolution (private DNS),
   the cost of transfer between zones and regions (ops-finops). Segmentation and private endpoints: sec-cloud-security.
5. **Central logs and tools.** Separate accounts/projects: **log archive** (write-only, retention, protection against
   deletion) and **security tooling** (CSPM, detection; a delegated administrator). Trails/diagnostic settings
   enabled *by the foundation*, not by the teams. What exactly to log and how to detect: sec-cloud-security,
   ops-security-operations; application telemetry: ops-observability.
6. **Guardrails as policies.** Two kinds, both in the design:
   - **preventive**: SCP, Azure Policy with the Deny effect, Organization Policy — they block the action;
   - **detective**: Config rules, Azure Policy with Audit, CSPM — they report non-compliance.
   Principle: blocking only where there is no legitimate exception (e.g. disabling audit logs); the rest is detection
   with an owner and a deadline. Every guardrail goes in in **audit mode** (usually 2–4 weeks [example]), then
   blocking. Exceptions: a register with an owner and an expiry date. The content of the guardrail list: sec-cloud-security.
7. **Tagging and costs.** A minimal tag set enforced by policy: `team`, `env`, `project`, `cost-center`,
   `data-class`, `expires` (for temporary ones). The cost tag activated in the billing tool; the account/subscription
   is the *first* allocation dimension, tags the second. Model: showback first, chargeback when the data is reliable.
   Budgets and anomalies, cleanup: ops-finops.
8. **Account vending.** A new account/subscription is created from a request (a PR to a YAML/HCL file or a form → PR), not
   from the console. Input: name, owner, environment, workload type, cost center, CIDR from the registry. Output:
   an account in the right group, SSO roles, a budget and alerts, tags, a connection to the hub, the baseline, a separate
   identity field for the pipeline (OIDC). Implementation: Account Factory for Terraform / customizations, Azure subscription
   vending (the reference module), the project factory in GCP. The time from request to
   a usable account is a foundation metric (target [example]: < 1 working day).
9. **Baselines per workload type (golden baselines).** A small number of profiles, e.g. `web-app`, `data-platform`, `batch`,
   `regulated`; each is a set: network, roles, policies, logs, backup, budget. The profile is chosen at vending. Do not
   multiply profiles: a new one is created only after the third repeated exception.
10. **Evolution and versions.** The landing zone is a product: a backlog, an owner, versions (SemVer: core-semver; a change of
    a blocking guardrail = a major for consumers). Changes rolled out in waves (test accounts → sandbox → nonprod →
    prod), with a change note and a rollback plan. Measuring drift (accounts outside the baseline) and migrating accounts to the new version
    is an ongoing process. Existing accounts: ops-cloud-migration (relocation into the hierarchy).
11. **Record.** A design document + a decision list; each decision: the question, the choice, the rejected options, the owner,
    the review date. The result is `proposed` for a human's approval.

## Decision list format
| ID | Decision | Choice | Rejected | Owner | Review |
|---|---|---|---|---|---|

## Example
**Situation:** "We have 20 teams, AWS as the main cloud, a small Azure for one application. Accounts are created by emailing the admin."
**Result** (a fragment, numbers [example]):

| ID | Decision | Choice | Rejected | Owner | Review |
|---|---|---|---|---|---|
| D-01 | AWS starting point | Control Tower + Account Factory for Terraform | a custom Organizations script (maintenance cost) | platform | 2027-04 |
| D-04 | Network | Transit Gateway, hub with a firewall, CIDR from the registry /16 per environment | full-mesh peering (grows quadratically) | networks | 2027-04 |
| D-07 | Guardrail on disabling logs | preventive (SCP), no exceptions | detective (too late) | security | yearly |
| D-09 | Tags | `team`, `env`, `cost-center`; missing = refusal in vending | a manual requirement in the wiki | finance | 2027-01 |

Azure: a separate case, without a full platform up to 3 applications; it goes under the same IdP and CIDR registry.

## Pitfalls
- A foundation built "in full" before the first workload: start from a minimal core and the first customer.
- Guardrails in blocking mode right away: teams bypass them or lose trust in the platform.
- Manual accounts next to vending: neither the baseline nor billing will cover them.
- Version skew: 40 accounts on 5 baseline versions; measure and migrate.

## Checklist
- [ ] starting point chosen and the product name checked in the documentation
- [ ] hierarchy by policies, account boundary = workload × environment, management account empty
- [ ] SSO from one IdP, no local users
- [ ] CIDR registry before the first network; topology and hub owner recorded
- [ ] log archive and security tooling accounts, logs enabled by the foundation
- [ ] guardrails: kind (preventive/detective), audit mode, exception register
- [ ] tags enforced, cost allocation by account and tags
- [ ] vending with IaC, a time-to-account metric, baseline profiles
- [ ] versioning and rollout waves for foundation changes

## Sources
- AWS Control Tower, Account Factory, Landing Zone Accelerator on AWS — AWS documentation; preventive (SCP), detective
  (Config), proactive (CloudFormation hooks) controls confirmed by search 2026-10-17, documentation pages not directly reachable
- Microsoft Learn: Cloud Adoption Framework, Azure landing zones (platform and application landing zones, subscription
  vending); search 2026-10-17
- Google Cloud: enterprise foundations blueprint, folder organization, Shared VPC, hub-and-spoke topology
  (docs.cloud.google.com/architecture); search 2026-10-17
- Limits (group depth, number of spokes, peering) [unverified]; check before the design.
