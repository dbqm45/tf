# Zero Trust architecture: PDP/PEP, ZTNA, VPN, SASE/SSE

Contents: components · patterns · ZTNA vs VPN · SASE and SSE · pitfalls

## Components (NIST SP 800-207)
- **Policy engine** (evaluates the request against the policy and the signals) + **policy administrator** (issues the token/establishes the session)
  = PDP. The **PEP** sits on the path to the resource (an agent, a gateway, a proxy) and closes the session on the PDP's command.
- Signal sources: the IdP, device management (MDM/EDR), the SIEM, threat intelligence, compliance policies,
  data classification, access logs.
- Requirement: the PEP is the only path; the PDP is highly available (a failure → a "fail closed" plan for critical resources
  and a controlled emergency mode for the rest, recorded in an ADR).

## Deployment patterns
1. Based on enhanced identity governance (policy from identity and groups).
2. Microsegmentation (gateways or host agents around resources).
3. A software-defined perimeter (SDP), i.e. a network that is "invisible" until the PDP allows it.
You usually combine the patterns; the choice depends on whether web applications, legacy protocols or servers dominate.

## ZTNA vs VPN
| | VPN | ZTNA |
|---|---|---|
| scope after logging in | a segment or the whole network | a single application |
| decision | once at connection | per session, from posture and context |
| lateral movement | made easier | limited |
| visibility | IP addresses | user, application, device |
| risk | stolen credentials give broad access; the VPN gateway is an attack target | dependence on the broker and the IdP |
Agentless ZTNA (browser) fits BYOD and partners, with an agent for non-HTTP protocols. Migration: one
application at a time, with the VPN in parallel until confirmed.

## SASE and SSE (definitions per Gartner, [unverified] in the source)
- **SASE** — a cloud service combining the network (SD-WAN) with security functions.
- **SSE** — the security part of SASE without the network: usually SWG (secure web gateway), CASB (SaaS control)
  and ZTNA, often with DLP. Use the names as a description of functions; check what the vendor really offers.

## Pitfalls
"Zero Trust" as a product name; ZTNA before putting identity in order; policies too detailed, so bypassed
with exceptions; no plan for a PDP failure; trusting posture reported by the device itself without attestation.
Threats and resilience: `arch-threat-modeling`, `ops-security-operations`.
