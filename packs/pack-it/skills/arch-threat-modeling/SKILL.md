---
name: arch-threat-modeling
description: Use for a threat model of a feature or integration — a DFD with trust boundaries, STRIDE, PASTA, risk assessment.
metadata:
  review: "2027-10-17"
  catalog: "Use when designing a feature, service or integration and when trust boundaries change — the threat model (a DFD with trust boundaries, the attack surface, STRIDE per element, PASTA for critical processes), risk assessment and quantification, risk decisions, OWASP Top 10:2025. Not for reviewing a specific diff (security-reviewer) or responding to an incident (ops-security-operations)."
  keywords: "obrona w głąb, defence in depth, defense in depth, warstwy obrony, warstwy zabezpieczeń, blast radius, wyciek danych, atak, zagrożenie, ryzyko, ryzyko rezydualne, czy ochrona się opłaca, koszt zabezpieczeń, FAIR, prawdopodobieństwo i strata, oszacować ryzyko liczbowo, ryzyko liczbowo zamiast wysokie średnie, czy warto wydać na ochronę, ochrona przed wyciekiem danych klientów, threat model, layers of defence, security layers, data leak, attack, threat, risk, residual risk, is protection worth it, cost of security, likelihood and loss, quantify risk, numeric risk instead of high medium, is it worth spending on protection, protecting customer data from leaks, STRIDE, trust boundaries"
---

# Threat modelling

Four questions (A. Shostack): **What are we building? What can go wrong? What are we going to do about it? Did we do a good job?**
A threat model is made during design, not after deployment, and updated with changes. The result is the file
`docs/project/04-architecture/threat-model.md` (core-project-record), not a conversation.

## When (triggers)
A new service or external integration; a new entry point (a public endpoint, a webhook, an upload, a queue from a partner);
a change of authentication, sessions, permissions or cryptography; a new data category (personal, payment, health);
a new AI agent with tools (core-agent-security). A small change without new flows → an update of the existing
model in the review, without a new workshop.

## Procedure
1. **Scope and goal.** What is in the model, what is outside it; the assets (data, money, reputation, availability) and who protects them.
   The security requirements from `requirements.md` and the quality attributes (arch-quality-attributes).
2. **A data flow diagram (DFD)** in Mermaid: external entities (a user, a partner, an IdP), processes (services, functions),
   data stores, flows with a label (what flows, the protocol) and **trust boundaries** (internet | DMZ | application network |
   data | cloud account | browser). Every boundary crossing is a threat candidate.
3. **The attack surface**: a list of entry and exit points (login, admin panels, search, forms, APIs,
   files, integrations, operational and monitoring channels), each with: who has access (anonymous / user / admin / service),
   what data it accepts, what control. First what is reachable from the internet, and critical code (auth, crypto, permissions).
4. **STRIDE per element** — for every DFD element the questions from the table below. Record a threat as a scenario:
   "An attacker [who] can [what] through [how], because [the missing control], consequence: [the asset]".
5. **Risk assessment** (the section below) and a **decision** for every threat: *mitigate* (a control + a test), *eliminate*
   (remove the feature or the flow), *transfer* (a provider, insurance, a contract), *accept*. Accepting a risk
   and transferring it are a human's decisions with an owner and a review date — the agent proposes them, it does not make them.
6. **Controls for the backlog and tests**: every mitigation has a task and an abuse case test, e.g. "user B
   downloads user A's invoice → 404". They go into the plan (core-project-record) and to qa-test-design.
7. **Verification**: does every flow across a trust boundary have S/T/I threats, does every data store have I/T/D,
   does every defence layer (network, identity, host, application, data, supply chain, detection, response) have
   a control or a recorded decision (`references/defense-layers.md`), does every decision have an owner.
   A `proposed` model → a human's acceptance.

## STRIDE per element (after Microsoft / Shostack)
| DFD element | S spoofing | T tampering | R repudiation | I information disclosure | D denial of service | E elevation of privilege |
|---|---|---|---|---|---|---|
| external entity | ✓ | | ✓ | | | |
| process | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| data store | | ✓ | (✓ audit logs) | ✓ | ✓ | |
| data flow | | ✓ | | ✓ | ✓ | |
| Typical control | authentication | integrity (a signature, a MAC, validation) | an audit log, a signature | encryption, authorization, minimization | limits, isolation, autoscaling with an upper limit | authorization, least privilege |

## PASTA — when the business impact matters
Seven stages, driven from the business goals: (1) business and security goals, (2) the technical scope,
(3) application decomposition (a DFD), (4) threat analysis (who attacks and why — data on real attacks in the industry),
(5) vulnerability and weakness analysis, (6) attack modelling (attack trees), (7) risk and impact analysis.
Apply it to critical processes (payments, settlements, medical data) and when the business makes the decision; day to day
STRIDE is enough.

## Risk assessment and quantification
- **Qualitatively (by default)**: likelihood (reachability from the internet, the required permissions, complexity, whether there is
  a ready exploit) × impact (data, money, availability, scope) on a 1–3 or 1–5 scale. Risk = the product; the action threshold
  recorded in an ADR.
- **Quantitatively (for budget decisions)**: FAIR — loss event frequency × loss magnitude, given as ranges
  (min, most likely, max) and a Monte Carlo simulation. Result: the annual loss in a range, comparable
  with the cost of the control. Numbers from data (incidents, the industry), not from one person's intuition.
- You record the risk after the control (residual) separately — that is what goes to acceptance.

## Error classes to check — OWASP Top 10:2025
A01 Broken Access Control · A02 Security Misconfiguration · A03 Software Supply Chain Failures (ops-supply-chain-security)
· A04 Cryptographic Failures (ops-secrets-identities, `cryptography-and-pki.md`) · A05 Injection · A06 Insecure Design (this
skill) · A07 Authentication Failures (be-auth-security) · A08 Software or Data Integrity Failures · A09 Security Logging
and Alerting Failures (ops-security-operations) · A10 Mishandling of Exceptional Conditions (fail closed, no leaking of
details in errors). For APIs: the OWASP API Top 10 in be-api-design.

## Template of the `threat-model.md` file
The artifact header (core-project-record) + sections: Scope and assets · DFD (Mermaid) · Attack surface (a table) ·
Threats (ID, element, STRIDE, scenario, likelihood, impact, risk, decision, control, test, owner) ·
Accepted risks (who, until when) · Assumptions · Open questions · Handoff.

## Example
**Situation:** "A payment operator sends payment confirmations to our webhook; after it the order goes to shipping."
**Result** (a fragment of `threat-model.md`, a 1–3 scale):

| ID | Element | STRIDE | Scenario | R | Decision and control | Abuse case test |
|---|---|---|---|---|---|---|
| T-1 | operator → webhook | S | An attacker sends a fake confirmation, because we do not verify the sender; consequence: goods without payment | 9 | mitigate: a signature (MAC) | no signature → 401, state unchanged |
| T-2 | operator → webhook | T | Replaying a signed request; consequence: double booking | 4 | mitigate: deduplication by id | the same request 2× → 1 effect |

More examples: `references/examples.md`.

## Checklist
- [ ] a DFD with trust boundaries and flow labels
- [ ] every entry point from the internet on the attack surface list
- [ ] STRIDE for every element crossing a boundary
- [ ] every threat with a decision; acceptances with an owner and a date (only a human)
- [ ] controls in the backlog and abuse case tests in the test plan

## Sources
- A. Shostack, *Threat Modeling: Designing for Security* (2014); [OWASP Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process),
  [OWASP Attack Surface Analysis Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html)
- PASTA — T. UcedaVélez, M. Morana, *Risk Centric Threat Modeling* (2015); FAIR — J. Freund, J. Jones, *Measuring and Managing Information Risk* (2014)
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/); [roadmap.sh — DevSecOps](https://roadmap.sh/devsecops)
Described in our own words.
