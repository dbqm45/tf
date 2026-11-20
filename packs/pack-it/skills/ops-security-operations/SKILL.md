---
name: ops-security-operations
description: Use for detecting and handling a security incident — SIEM, EDR, patches, NIST 800-61, forensics.
metadata:
  review: "2027-04-17"
  catalog: "Use for threat detection and security incident response — SIEM, alerts and rules as code, EDR, IDS/IPS, SOAR with a human gate, vulnerability and patch management, host hardening (CIS, SSH, firewall, auditd, drift), the response lifecycle (NIST SP 800-61r3), containment, evidence preservation, root cause analysis, notifications. Not for outages without an attack (ops-sre-incidents) or security design (arch-threat-modeling)."
  keywords: "centralne logi, zbieranie logów w jednym miejscu, zarządzanie logami, NIST SP 800-92, integralność logów, brak logów, utwardzanie serwera, hardening, CIS Benchmark, SSH tylko klucze, PermitRootLogin, OpenSCAP, Lynis, auditd, unattended-upgrades, wyciek danych osobowych klientów, w jakich terminach zgłosić incydent, kto przygotowuje zgłoszenie incydentu, centralized logs, collecting logs in one place, log management, log integrity, missing logs, server hardening, SSH keys only, customer personal data leak, incident notification deadlines, who prepares the incident notification"
---

# Security operations: detection and response

Prevention will fail at some point. This skill is about how to notice it and what to do next. Network, cloud, segmentation,
DDoS and CSPM: `references/network-and-cloud.md`. A catalog of attacks with signals
and controls, analysis models (Kill Chain, ATT&CK, the diamond model), threat hunting, intelligence and decoys:
`references/attacks-and-analysis.md`. Forensics (order of volatility, chain of custody) and penetration tests with rules
of engagement: `references/forensics-and-penetration-testing.md`. Hardening the server's operating system (CIS baseline, SSH,
accounts, host firewall, audit, drift checking): `references/host-hardening.md`. Mapping onto SOC 2, ISO 27001 and NIST CSF: `references/compliance.md`.

## 1. Security telemetry
- Sources (most important first): the IdP and sign-ins (successes, failures, MFA, method changes), cloud audit logs (control-plane
  API, IAM), application logs with security events (authorization denials, permission changes, exports, use of
  API keys), Kubernetes audit, CI/CD (who ran it, what was deployed), DNS and outbound traffic, EDR from servers and
  workstations, WAF and the API gateway.
- Logs **outside the system they describe** (an attacker with root deletes local logs), with UTC time and clock
  synchronization, retention set together with legal and investigative requirements (usually months, not days). No sensitive
  data (ops-observability).
- **A log management plan** (per NIST SP 800-92), before you choose a SIEM: an inventory of sources with an owner,
  priority and format; transport with a buffer (an agent or collector, a queue), so that a receiver failure does not lose
  events; **integrity** — storage in a store protected against deletion (object lock, WORM), separated
  permissions (the source system only appends, production administrators do not delete logs); retention per source
  (fast access for a short time, an archive for longer); **an alarm when a source stops sending** — silence in the logs is also a signal
  (a failure or an attacker). The format of security events in the application: OWASP Logging Cheat Sheet.
- **A SIEM** collects, normalizes and correlates. The value comes only from the rule set and its maintenance, not from the deployment itself.

## 2. Alerts and rules as code
| Type | Example | Note |
|---|---|---|
| signature / rule | a login with `alg: none`, a known IoC (hash, domain) | fast, easy to evade |
| threshold | > 20 failed logins per account in 5 min | pick the threshold from data, not off the top of your head |
| anomaly | an export 10× larger than usual, a login from a new country | needs a baseline; many false alarms at the start |
| correlation | new MFA + password reset + new API token within 10 min | the most valuable; combines weak signals |
- Rules in a repository (a vendor-neutral format, e.g. Sigma), review in a PR, a test on recorded events
  and a mapping onto MITRE ATT&CK techniques — you know what we do not detect yet.
- Every alert: severity, runbook, owner. Measure precision (the false alarm rate) and time to response; an alert
  ignored for a month → fix it or remove it (alert fatigue is a security gap).

## 3. EDR, IDS/IPS, WAF
- **EDR** on servers and laptops (processes, connections, files, host isolation with one command); in Kubernetes
  runtime detection (e.g. Falco: a shell in a container, unexpected connections, writes to system paths).
- **IDS** detects and alerts, **IPS** blocks inline (the risk of blocking legitimate traffic — start in detection mode).
- **WAF** in front of public applications as an additional layer (OWASP CRS rules, bot protection), never instead of
  validation and authorization in the code.

## 4. SOAR — automation with a gate
- Automate fully: alert enrichment (who, which host, IP reputation, recent changes), ticket creation,
  evidence collection, notifying the on-call person.
- With human approval: isolating a production host, disabling an account, revoking all sessions, blocking
  a partner's IP — the side effects can be bigger than the attack. An exception agreed in advance: e.g. automatic revocation of
  a key found publicly in a repository.
- Playbooks versioned like code and exercised. An AI agent may enrich and propose, it does not perform destructive actions
  (ops-sre-incidents, autonomy levels; core-agent-security).

## 5. Vulnerabilities and patches
1. **An asset inventory** (hosts, images, functions, domains, dependencies — SBOM) — you will not patch what you do not know about.
   Every host has a hardening baseline and checked drift (`references/host-hardening.md`).
2. **Regular scanning**: hosts and the network (e.g. OpenVAS, Nessus, Qualys), images and dependencies (ops-supply-chain-security),
   cloud configuration (CSPM), the application (DAST on staging). An external scan from the internet's perspective.
3. **Priority** not from CVSS alone: a vulnerability exploited in practice (e.g. the CISA KEV list), the probability of
   exploitation (EPSS), reachability from the internet, the asset's value (ops-supply-chain-security: priorities).
4. **Remediation deadlines** per level (e.g. exploited and public: days; critical: 2 weeks; the rest: the cycle) with exceptions
   recorded and reviewed.
   A vulnerability of an application framework (e.g. React Server Components, Next.js) is also an architectural decision: server-side
   component code, a patch deadline within a day for critical CVEs and containment are described in
   fe-architecture (client and server component security).
5. **Automatic patching** in rings: the test environment → canary → the rest, with a test after the patch and the ability to
   roll back. In immutable infrastructure a "patch" is an image rebuild and a deployment, not logging in to the machine.

## 6. Responding to a security incident
Per NIST SP 800-61r3 (04.2025), response is part of risk management according to the six CSF 2.0 functions
(Govern, Identify, Protect, Detect, Respond, Recover). Preparation and lessons learned are continuous, they are not just the first
and the last phase.
1. **Preparation**: roles (incident commander, technical, communication, legal), a channel outside the attacked systems,
   contacts (the cloud provider, CERT, the insurer), playbooks for typical scenarios (a compromised account, a leaked key,
   ransomware, a malicious dependency — ops-supply-chain-security), "dry run" exercises.
2. **Detection and analysis**: confirm, the scope (which accounts, hosts, data), a timeline in UTC, severity. Assume that
   the attacker can read the usual channels (e-mail, chat) — move sensitive findings to the emergency channel.
3. **Preserving evidence against changes**: disk snapshots, a memory dump if possible, a log export, copies of
   tokens and artifacts to read-only storage; a chain of custody (who, when, what, checksum). Do not shut down
   the machine without need — you lose the memory.
4. **Containment**:
   - the source — block the attacker's addresses and accounts;
   - the technique and access — revoke credentials, sessions and keys, rotate secrets;
   - the target — isolate the host with a security group or EDR, cut off the resource.
   Short-term fast, long-term durable; be careful not to reveal the detection to the attacker before you establish the scope.
5. **Eradication**: the cause and all persistence points (accounts, keys, cron jobs, images, webhooks,
   OAuth applications); rebuild from trusted sources instead of "cleaning" the machine.
6. **Recovery** from backups taken before the incident, heightened monitoring, a gradual return of traffic.
7. **Lessons learned**: a blameless root cause analysis (ops-sre-incidents) — the technical cause, contributing factors,
   why detection took as long as it did; actions with an owner; new detection rules from this incident.
- **Notifications** — deadlines counted from discovery: GDPR (RODO) Art. 33 — the supervisory authority within 72 h (a personal data breach);
  NIS2 — an early warning within 24 h, a notification within 72 h, a final report within a month (covered entities). The decision
  and the content of the notification are prepared by a human with the legal department; the agent supplies the timeline and the facts.

## Checklist
- [ ] security logs off the host, UTC, retention set; storage protected against deletion, an alarm on missing logs
- [ ] detection rules in the repo, with a test, an owner and a runbook; measured precision
- [ ] an asset inventory and vulnerability remediation deadlines; patching in rings
- [ ] hosts hardened against a baseline (CIS), drift checked with a scanner
- [ ] incident playbooks exercised; the emergency channel and contacts ready
- [ ] destructive automation only with human approval

## Sources
- NIST SP 800-92 *Guide to Computer Security Log Management* (2006); Rev. 1 *Cybersecurity Log Management Planning
  Guide* — a draft of 11.10.2023, not final (per a search on 2026-10-27);
  [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) (content [unverified])
- [NIST SP 800-61 Rev. 3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf) (04.2025),
  [AWS Security Incident Response Guide — containment](https://docs.aws.amazon.com/whitepapers/latest/aws-security-incident-response-guide/containment.html)
- [roadmap.sh — DevSecOps](https://roadmap.sh/devsecops) (SIEM, SOAR, EDR, IDS/IPS, alert types, IR lifecycle,
  containment, forensics, RCA, automated patching)
Described in our own words.
