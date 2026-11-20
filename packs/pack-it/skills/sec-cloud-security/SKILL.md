---
name: sec-cloud-security
description: Use for AWS, Azure, GCP cloud security — the shared responsibility model, account guardrails, logs, CSPM and CNAPP, CIS, baseline.
metadata:
  review: "2027-04-17"
  catalog: "Use when designing or reviewing the security of a public cloud (AWS, Azure, GCP) — shared responsibility (IaaS, PaaS, SaaS), the structure of accounts, subscriptions and projects with guardrails (SCP, Azure Policy, Organization Policy), identity without long-lived keys, network segmentation and private endpoints, encryption with customer keys, data classification, a logging baseline, CSPM, CNAPP and CIEM, CIS benchmarks, containers in the cloud, policies as code, incident readiness. The result is a baseline document and a control mapping. Not for Terraform itself, RBAC and NetworkPolicy (ops-kubernetes), OIDC in CI and secrets (ops-secrets-identities), zero trust and human identities (sec-zero-trust-identity), costs (ops-finops) or incident handling (ops-security-operations)."
  keywords: "bezpieczeństwo chmury, cloud security, baseline chmury, landing zone, współdzielona odpowiedzialność, shared responsibility, SCP, Azure Policy, Organization Policy, guardrails, publiczny bucket, CloudTrail, Activity Log, Cloud Audit Logs, CSPM, CNAPP, CIEM, CIS Benchmark, prywatny endpoint, private link, VPC, VNet, klucze klienta, CMK, KMS, Checkov, Conftest, break-glass, mapowanie kontroli, multi-cloud, audyt chmury, cloud baseline, public bucket, private endpoint, customer keys, control mapping, cloud audit"
---

# Cloud security: baseline and control mapping

The output: the file `docs/project/04-architecture/cloud-security-baseline.md` (core-project-record) with two parts:
**the baseline** (what applies to every account, subscription and project) and **the control mapping** (control → AWS / Azure / GCP
→ how it is enforced → how it is verified → owner). The output table and the service equivalents are given in
`references/control-mapping.md`. This skill deploys nothing: changes in the cloud go through
IaC with a plan in the PR and a human's approval.

## Procedure
1. **Scope and service types.** List the clouds and services in use, mark each as IaaS / PaaS / SaaS. The provider is responsible
   for the security *of the cloud* (physical facilities, the hypervisor; in PaaS also the operating system and the runtime),
   the customer for security *in the cloud*. Always on the customer's side: data, identities and permissions, the configuration
   of services. The closer to IaaS, the more on the customer's side (the operating system, patches, the host network). Record the boundary per service.
2. **Structure and guardrails.** The hierarchy: organization → groups (OUs, management groups, folders) → accounts, subscriptions
   or projects, separately for: production, non-production, logs (an account write-only, read by security),
   security tools and the shared network. Preventive guardrails at the top of the hierarchy:
   - AWS: **SCP** (Service Control Policies) in Organizations. They limit the maximum permissions, grant nothing
     and **do not cover the management account**, so do not run workloads in it.
   - Azure: **Azure Policy** (the Audit, Deny, DeployIfNotExists effects) assigned to a management group, plus RBAC.
   - GCP: **Organization Policy** (constraints, e.g. `constraints/iam.disableServiceAccountKeyCreation`,
     `constraints/storage.publicAccessPrevention`).
   Typical guardrails: a ban on disabling audit logs, a ban on leaving the organization, a restriction of regions,
   a ban on public access to storage, a requirement for encryption. Introduce them in audit mode, then the blocks.
3. **Identity.** People through SSO with phishing-resistant MFA (details: sec-zero-trust-identity). Workloads without
   long-lived keys: roles (AWS IAM roles), managed identity (Azure), service accounts with identity attachment
   (GCP); external systems and CI through OIDC federation (ops-secrets-identities). Disable the creation of service account
   keys. Just-in-time permissions, a review of unused ones (IAM Access Analyzer, Entra Permissions
   Management or an equivalent, IAM Recommender). **Break-glass**: 2 emergency accounts outside SSO, the password in a vault
   split between two people, hardware MFA, an alarm on every login, a test every quarter [example].
4. **Network.** Separate networks (VPC, VNet) per environment, public subnets only for load balancers and gateways; databases
   and internal services without public addresses. Private endpoints to PaaS services (AWS PrivateLink / VPC
   endpoints, Azure Private Endpoint, GCP Private Service Connect) and the service's public access disabled. Egress
   closed by default, with an allowlist (a firewall or a proxy) and control of the instance metadata (AWS: IMDSv2 required,
   the account default setting for new instances). Management without SSH and RDP open to the internet (SSM,
   Bastion, IAP). Protection against exfiltration through APIs: GCP VPC Service Controls, AWS endpoint policies.
5. **Data.** Classification (public, internal, confidential, regulated) in a resource tag; the class decides the key,
   location and retention. Encryption at rest is the default today in most services; enable **customer-managed
   keys** (KMS, Key Vault, Cloud KMS) for the confidential and regulated classes, with a separate key owner,
   rotation and a ban on deletion without a waiting period. Public storage: AWS S3 Block Public Access on the account and in an SCP,
   Azure anonymous access to containers disabled, GCP Public Access Prevention. Backups in a separate
   account with a deletion lock (immutability). Personal data: arch-privacy-compliance.
6. **Logging and detection.** The management plane audit log always, to a separate log account,
   with retention and protection against deletion:
   - AWS **CloudTrail**: the event history is 90 days of management events per region; an organization trail (all accounts
     and regions), log file integrity validation, data events (S3, Lambda) for confidential resources.
   - Azure **Activity Log**: 90 days by default; a diagnostic setting to Log Analytics and a storage account.
   - GCP **Cloud Audit Logs**: Admin Activity always enabled and cannot be disabled; **Data Access** disabled by default
     (the BigQuery exception: [unverified]), so enable it for projects with confidential data.
   On top of that, network flow logs, DNS, load balancing and data service logs. Detection rules and alert
   handling: ops-security-operations; application telemetry: ops-observability.
7. **Posture.** CSPM in short: continuous checking of the configuration against a benchmark (AWS Security Hub, Microsoft Defender
   for Cloud, Google Security Command Center, Prowler). **CIEM**: analysis of permissions and excessive access.
   **CWPP**: protection of workloads (machines, containers, functions). **CNAPP**: a platform combining CSPM, CIEM, CWPP,
   an IaC scan and context (attack paths); it is a Gartner market category, the scope depends on the vendor
   [unverified: the official definition]. From a CNAPP vendor require: coverage of all accounts, attack paths with context
   (exposure + permissions + vulnerability), an export of results, not just a dashboard. Benchmarks: CIS Foundations
   (separate for AWS, Azure, GCP), AWS Foundational Security Best Practices, Microsoft cloud security benchmark.
   Check the CIS version number before use. Every deviation has an owner and a date.
8. **Containers and Kubernetes.** A managed cluster with a private control plane or a limited address range,
   pod identity (IRSA / EKS Pod Identity, Azure Workload Identity, GKE Workload Identity), a private registry with
   scanning and signatures, nodes with a minimal operating system and auto-update. RBAC, NetworkPolicy and Pod Security: ops-kubernetes; images:
   ops-docker.
9. **Policies as code.** The order: an IaC scanner (**Checkov**) → your own policies in **OPA / Conftest** (Rego on the Terraform
   plan in JSON) → guardrails in the cloud as the last line. The same rule has one source; gates in the PR:
   the IaC plan. Drift and manual changes in the console are reported by CSPM.
10. **Incident readiness.** Before an incident: a forensic account (isolated), evidence snapshots, the response team's
    permissions granted in advance on a just-in-time basis, scenarios: a leaked key, an infected instance, a public bucket,
    a taken-over root / global administrator account. Procedures: ops-security-operations. The cost of logs: ops-finops.
11. **Record and verification.** Fill in the mapping table. Every control has a way of checking it (a CSPM query, a policy
    test, a review). The result `proposed` → a human's approval; exceptions to the baseline only by a human's decision.

## Example
**Situation:** "15 AWS accounts and 2 Azure subscriptions, developers have access keys, the bucket with invoices was public."
**Result** (a fragment of the mapping, numbers [example]):

| Control | AWS | Azure | Enforcement | Verification | Owner |
|---|---|---|---|---|---|
| K-03 no public storage | S3 Block Public Access | a ban on anonymous access to containers | SCP + Azure Policy (Deny) | CSPM, 0 critical findings | platform |
| K-07 no long-lived keys | roles + SSO federation | managed identity | an SCP forbids `iam:CreateAccessKey` | credential report, 0 keys > 90 days | identity |
| K-11 audit logs | an organization trail to the log account | Activity Log → Log Analytics | an SCP forbids `cloudtrail:StopLogging` | an alarm on stopping | security |

Plan: audit for 2 weeks → block; exceptions with an expiry date.

## Checklist
- [ ] every service marked IaaS / PaaS / SaaS, the responsibility boundary recorded
- [ ] an account structure with a log account; guardrails at the top of the hierarchy, audit mode first
- [ ] no long-lived keys; break-glass tested; just-in-time permissions
- [ ] private endpoints, egress with an allowlist, zero SSH and RDP from the internet
- [ ] data classification, customer keys for the confidential classes, public access blocked
- [ ] audit logs to a separate account; Data Access in GCP enabled where needed
- [ ] CSPM and a benchmark with a version; deviations with an owner and a date
- [ ] policies as code in the PR; a control mapping with a verification method

## Sources
- AWS: Organizations SCP, CloudTrail, S3 (the update of the default bucket settings: 2023-04-05), IMDSv2 as the default (2024-03); checked by search 2026-10-17, the documentation pages not directly accessible
- Google Cloud: Audit Logs, Organization Policy (security foundations blueprint), CIS GCP Foundation v5.0.0 (CIS, June 2026)
- Microsoft: Azure Policy, Activity Log (90 days), Private Link, Microsoft cloud security benchmark (MCSB v1)
- Checkov, Conftest and OPA — the projects' documentation; definitions of CNAPP, CSPM, CIEM, CWPP: Gartner (indirectly) [unverified]
