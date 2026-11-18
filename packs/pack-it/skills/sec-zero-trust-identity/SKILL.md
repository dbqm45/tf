---
name: sec-zero-trust-identity
description: Use for Zero Trust and identity as the perimeter — NIST 800-207, ZTNA instead of VPN, phishing-resistant MFA, PAM, device posture, the CISA maturity map.
metadata:
  review: "2027-04-17"
  catalog: "Use when you plan or assess a Zero Trust architecture — NIST SP 800-207 principles, policy decision and enforcement points (PDP/PEP), identity as the perimeter (workforce IAM, customer CIAM, PAM, just-in-time access), phishing-resistant MFA (FIDO2, passkeys), device posture, microsegmentation, ZTNA versus VPN, SASE/SSE, the CISA maturity model, a migration map and metrics. Not for OAuth/OIDC in application code (be-auth-security), machine identities and secrets (ops-secrets-identities), NetworkPolicy (ops-kubernetes), cloud security (sec-cloud-security) or a feature threat model (arch-threat-modeling)."
  keywords: "zero trust, ZTNA, VPN, nigdy nie ufaj, zawsze weryfikuj, perymetr, segmentacja, mikrosegmentacja, SASE, SSE, CASB, SWG, 800-207, PDP, PEP, passkey, FIDO2, WebAuthn, phishing, MFA, PAM, JIT, dostęp na żądanie, IAM, CIAM, stan urządzenia, device posture, dojrzałość zero trust, CISA ZTMM, ruch boczny, lateral movement, tożsamość agenta, agenci ai wywołują api, jedno konto usługi, konto usługi dla agentów, spiffe, spire, svid, dpop, token exchange, w imieniu użytkownika, never trust, always verify, perimeter, segmentation, microsegmentation, on-demand access, device state, zero trust maturity, agent identity, ai agents call apis, single service account, service account for agents, on behalf of the user"
---

# Zero Trust and identity

**Boundary.** The skill concerns the architecture and the program: who, from which device, gets access to what and on what
conditions. OAuth/OIDC, sessions and tokens in code: `be-auth-security`. Machine identities, secrets, OIDC for CI:
`ops-secrets-identities`. NetworkPolicy and mTLS in the cluster: `ops-kubernetes`. Cloud account security:
`sec-cloud-security`. Threats to a specific feature: `arch-threat-modeling`. Algorithms and certificates:
`sec-cryptography-pki`. Zero Trust is a strategy, not a product: no purchase "turns it on". Dropping the VPN means
a policy enforcement point (PEP) in front of every application; access is decided by a policy decision point (PDP) based on
identity, device state and context (NIST SP 800-207).
Result: `docs/project/04-architecture/zero-trust.md` (core-project-record) with a state map, a plan and metrics.

## Foundation: NIST SP 800-207 (August 2020)
Seven tenets, in short:
1. Every data source and service is a resource.
2. All communication is secured regardless of network location.
3. Access to a resource is granted per session.
4. Access follows from a dynamic policy (identity, application, device, context).
5. The organization monitors the integrity and posture of all assets.
6. Authentication and authorization are dynamic and strict before access is granted.
7. The organization collects data on the state of assets, the network and communication and uses it to improve security.
Details and the wording of the tenets [unverified] in the primary source (NIST page unreachable from the sandbox, 2026-10-17).

The logical model: the **PDP** (policy decision point = policy engine + policy administrator) decides, the **PEP** (policy
enforcement point) enforces and is the only path to the resource. PDP inputs: the IdP and MFA, the device registry and posture,
threat intelligence, logs, data access policies. Deployment patterns: an identity-based agent/gateway,
microsegmentation, a software-defined perimeter (SDP). Decide which one fits the resources (`references/architecture-and-sase.md`).

## Procedure
1. **Resources and flows.** An inventory of applications, data, identities (people and machines), devices; a "who to what" map.
   Start from the **protect surface** (the most valuable data and services), not from the whole network.
2. **Baseline** per the CISA Zero Trust Maturity Model 2.0: five pillars (identity, devices, networks,
   applications and workloads, data), three cross-cutting capabilities (visibility and analytics, automation and orchestration,
   governance), four stages (Traditional, Initial, Advanced, Optimal). Assess each pillar separately, the pillars
   develop at different paces. The publication date of version 2.0 (April 2023) and any newer versions:
   [unverified].
3. **Identity as the perimeter** (priority no. 1, `references/identity-and-access.md`): one IdP with SSO, phishing-resistant
   MFA (FIDO2/WebAuthn, passkeys, hardware keys), CIAM for customers separated from the workforce directory,
   PAM and just-in-time access for administrative privileges, access reviews, fast access revocation.
   AI agents: their own workload identity for each instance (SPIFFE/SVID), the user's token bound to the agent's key
   (mTLS, DPoP), token exchange when crossing between services (`references/identity-and-access.md`, last section).
4. **Device:** a registry, disk encryption, an up-to-date system, EDR; the posture signal goes to the PDP, and a non-compliant
   device gets less, not "all or nothing". Private devices (BYOD) — access through the browser/VDI.
5. **Application access:** ZTNA per application instead of a VPN to the whole network; legacy applications behind an identity-aware
   proxy. The VPN stays only where ZTNA does not reach, limited to a segment and with a retirement plan.
6. **Segmentation:** microsegmentation around the protect surface, a default-deny rule for east–west traffic;
   in Kubernetes `ops-kubernetes`. Observation mode first, then blocking.
7. **Data and continuous verification:** classification, DLP, telemetry to the SIEM, automatic responses (session revocation,
   device quarantine) — `ops-security-operations`.
8. **The migration plan** (below) and **metrics**. The plan and the risk acceptance are approved by a human; the agent proposes.

## Migration map (stages, each with a completion criterion)
| Stage | Scope | Done when |
|---|---|---|
| 0 | inventory, protect surface, CISA assessment per pillar | map approved |
| 1 | IdP with SSO for all applications, phishing-resistant MFA for administrators | 100% of privileged accounts on FIDO2 |
| 2 | device registry and posture in the policy; PAM and JIT | no standing administrator privileges |
| 3 | ZTNA for the first 3–5 applications; a VPN retirement pilot | pilot without a rise in tickets |
| 4 | microsegmentation of the protect surface, telemetry to the SIEM | lateral movement blocked in enforcement mode |
| 5 | response automation, continuous assessment, quarterly review | metrics within thresholds |
The order may differ, but identity and MFA always before segmentation.

## Metrics
The share of accounts with phishing-resistant MFA (the target for privileged ones: 100%); standing privileged accounts vs JIT;
the share of applications behind ZTNA/SSO; the share of devices compliant with the policy; the median time to revoke access after offboarding;
the share of east–west traffic covered by policy; the time to detect and cut off a session; the number of policy exceptions and their age.
Every metric has an owner, a data source and a threshold; the thresholds below are [example] to be agreed.

## Example
**Input:** "A 400-person company, a VPN for everyone, phishing attacks on administrators, the ERP and the code repository
in the cloud. We want Zero Trust."
**Result** (a fragment of `zero-trust.md`):
- Protect surface: the ERP, the repository, the cloud console, the customer database.
- CISA assessment: identity Initial, devices Traditional, networks Traditional, data Traditional.
- Quarter 1: FIDO2 keys for 12 administrators; SMS disabled for privileged accounts [example]; JIT for the cloud console.
- Quarter 2: device registry and posture policy; the ERP and the repository behind ZTNA.
- Quarter 3: VPN phased out except for two industrial systems; microsegmentation of the customer database.
- Success metric: 0 standing administrator accounts, 100% of ERP access through ZTNA, access revocation time < 1 h [example].
- Risks: dependence on a single IdP (offline break-glass accounts with review), tickets from BYOD employees.

## Checklist
- [ ] protect surface and an inventory of identities, devices and applications
- [ ] assessment per CISA pillar, not one overall score
- [ ] phishing-resistant MFA for privileged accounts, then for everyone; SMS and push without number matching are out
- [ ] PAM and JIT, no standing administrator privileges; break-glass accounts
- [ ] device posture in the access decision; ZTNA per application; a VPN retirement plan
- [ ] microsegmentation first in observation mode; telemetry to the SIEM
- [ ] a stage map with completion criteria and metrics with owners

## Sources
- NIST SP 800-207, *Zero Trust Architecture* (August 2020) — the seven tenets via secondary sources, 2026-10-17 [unverified in the primary]
- CISA, *Zero Trust Maturity Model* v2.0 — pillars and stages via secondary sources, 2026-10-17 [unverified in the primary]
- FIDO Alliance (FIDO2, passkeys), SASE/SSE definitions (Gartner) — [unverified]
Described in our own words.
