# Attacks, analysis models and threat hunting

This file is for defense: recognizing the attack mechanism, the signals in the logs and the control that stops it. No
instructions for carrying out attacks.

## Catalog of attacks → signal → control
| Attack | Mechanism | Signal | Control (where in the factory) |
|---|---|---|---|
| **phishing** and variants: SMS (smishing), phone (vishing), targeting executives (whaling), impersonating a known person | phishing for login data, an OAuth consent or a bank transfer | a login from a new place right after a click, a new application consent, mail forwarding rules | phishing-resistant MFA (keys, passkeys), DMARC (ops-linux-networking), admin consent for scopes (be-auth-security), training with exercises |
| **password guessing**: brute force (many passwords on one account), spraying (one popular password on many accounts), credential stuffing from leaks | guessing or reusing a password | many failed logins per account (brute force) or per IP and password across many accounts (spraying), logins from proxy lists | limits per account and per IP, checking passwords against leaks, MFA, passwordless login |
| **session or token hijacking** (cookie theft, replay) | bypassing MFA with a stolen session | the same session from two countries, a new device fingerprint | short tokens, device binding, revocation (be-auth-security, `tokens-sessions-oauth.md`) |
| **traffic interception** (MITM, ARP or DNS spoofing, a rogue Wi-Fi access point) | eavesdropping on or modifying traffic | certificate warnings, unexpected ARP/DNS changes | TLS everywhere with HSTS, mTLS between services, DNSSEC for your own zones, 802.1X and segmentation (`network-and-cloud.md`) |
| **request replay** | resending a valid request | duplicate identifiers, old timestamps | a timestamp and a nonce in the signature, idempotency (be-api-design) |
| **injections and web flaws**: SQL, XSS, CSRF, path traversal (`../`), SSRF | input executed as code or a path | SQL errors in logs, unusual characters in parameters, requests to internal addresses | parameterized queries, output encoding and CSP, CSRF tokens and `SameSite`, path normalization and an allowlist, a host allowlist (be-auth-security, fe-architecture) |
| **memory errors** (buffer overflow) | a write outside a buffer in native code | process crashes, unusual input | memory-safe languages, up-to-date native libraries, system hardening (ops-docker) |
| **privilege escalation** | from a regular account to an administrator (misconfiguration, a vulnerability, sudo, SUID) | new permissions, root processes from an application container | least privilege, non-root containers, patches (ops-kubernetes, ops-docker) |
| **living off the land** (LOLBAS on Windows, GTFOBins on Unix) | the attacker uses built-in tools (PowerShell, `curl`, `certutil`) instead of their own malware | child processes of the application (a shell from a web server), download and execution in one line | EDR, a process allowlist, no tools in images (distroless); the factory hooks block, among others, `curl \| sh`, `irm \| iex`, `mshta` (core-agent-security) | <!-- audit-ok: opis ataku, nie polecenie -->
| **lateral movement in Windows/AD** (e.g. passing the password hash — pass-the-hash, attacks on Kerberos) | using a hash or a ticket instead of a password | logins with an account from an unusual host, many hosts in a short time | admin accounts only on privileged workstations, LAPS, restricting NTLM, segmentation, long random passwords for service accounts |
| **denial of service** (DoS, DDoS) | resource exhaustion | a spike in traffic, cost, 429/503 errors | `network-and-cloud.md` (DDoS), limits (be-api-design) |
| **supply chain poisoning**, typosquatting in package and domain names | a malicious dependency, a look-alike domain | a new transitive dependency, an install script | ops-supply-chain-security |
| **watering hole and browser attacks** (drive-by) | an infected site visited by the target | EDR, traffic to new domains | up-to-date browsers, isolation, a DNS filter |
| **zero-day** | a vulnerability without a patch | behavioral anomalies, not signatures | defense in depth, segmentation, fast patching after publication, behavior detection |
| **physical social engineering** (tailgating, shoulder surfing, dumpster diving) | bypassing safeguards through people | — | access control, screen lock, document shredding, training |

## Analysis models
- **Cyber Kill Chain** (Lockheed Martin): reconnaissance → weaponization → delivery → exploitation → installation →
  command and control → actions on objectives. Breaking any stage breaks the attack — map controls onto stages
  and look for stages without a control.
- **MITRE ATT&CK**: a detailed knowledge base of tactics (the attacker's goal) and techniques (the means), with detection and mitigation for
  each. It is used to map the coverage of detection rules (SKILL.md: rules as code) and to describe an incident in a common language.
- **The diamond model**: every event links the **adversary**, the **capability** (tool, technique), the **infrastructure**
  (domains, addresses) and the **victim**. From a known vertex you look for the others (e.g. from a C2 domain — other victims).
- **Alert classification**: true positive (attack detected), false positive (an alarm without an attack — a cost of attention),
  true negative, false negative (an undetected attack — the most dangerous, visible only in tests,
  exercises and hunting). A rule tuned only for fewer false alarms increases the number of misses.

## Threat hunting
It assumes the attacker is already in and has evaded the automation. The loop: **a hypothesis** (from ATT&CK, threat intelligence or
an anomaly — "someone is using a service account interactively") → **a query** in the logs and EDR → **a result**: a finding
(an incident) or nothing, but then **a new detection rule**, so that next time the automation does it.

## Threat intelligence and OSINT
- Sources: vendor and CERT bulletins, CISA KEV, industry reports, IoC feeds (STIX/TAXII formats). The valuable ones are
  those that concern your technology and industry.
- Checking suspicious domains, addresses and files in public services (VirusTotal, urlscan.io, ANY.RUN,
  Joe Sandbox, Whois): **do not upload files or addresses containing company or customer data** — in many of these
  services uploaded samples and results are visible to other users. First search by the file hash; dynamic
  analysis in the organization's private sandbox.
- Decoys: honeypots (fake systems), honeytokens and canary tokens (fake API keys, database records, files),
  every use of which is a high-confidence alarm; a DNS sinkhole redirects known malicious domains to a server
  controlled by the defense.

## Sources
- [Lockheed Martin — Cyber Kill Chain](https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html);
  [MITRE ATT&CK](https://attack.mitre.org/); S. Caltagirone et al. — The Diamond Model of Intrusion Analysis (2013)
- [LOLBAS Project](https://lolbas-project.github.io/); GTFOBins; [roadmap.sh — Cyber Security](https://roadmap.sh/cyber-security)
  (attacks, threat hunting, threat intel, OSINT, honeypots, sinkholes, false/true positives, malware, sandboxing)
Described in our own words.
