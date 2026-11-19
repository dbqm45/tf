# Post-incident forensics and penetration testing

## Forensics — principles
- **Order of volatility** (RFC 3227): first what disappears fastest — registers and cache, RAM
  (processes, connections, keys), network state, processes; then disks, remote logs, backups, archival media.
  Shutting down the machine erases the memory, which often holds the only trace.
- **Do not work on the original**: a disk image (e.g. `dd`, FTK Imager) or a volume snapshot in the cloud, a memory dump
  with an acquisition tool, a hash (SHA-256) of the image at acquisition and at every use; analysis on a copy, in an isolated
  environment.
- **Chain of custody**: who, when, from where, with which tool collected the evidence, where it was stored, who had access.
  Without it the evidence may have no value in a dispute or proceedings.
- **A timeline** in UTC from many sources (system and application logs, cloud logs, EDR, firewalls, mail) — clock
  synchronization is a precondition (ops-security-operations: telemetry).
- Analysis tools (e.g. Autopsy, Volatility for memory, hex editors) are operated by a trained person; in a serious
  incident or with possible legal proceedings — an external response team (the contact from the plan).
- The agent's role: it collects and organizes facts, builds the timeline from logs, keeps the evidence list; it does **not** change the state
  of the attacked systems without a decision by the incident commander (SKILL.md: response).

## Penetration tests and team exercises
- **Rules of engagement** in writing, **before** the test: the written consent of the systems' owner,
  the scope (addresses, domains, applications, accounts) and exclusions, allowed techniques (e.g. no DoS, no social engineering), time
  windows, emergency contacts and conditions for immediate termination, handling of data found during the test,
  the way of reporting and removing the test's artifacts.
- Cloud provider and SaaS systems: only within their testing policies (most large providers publish them).
- Teams: **red** (attacks according to a scenario), **blue** (defends and detects), **purple** (both together,
  improving detection test by test). The result of an exercise is new rules and fixes, not just a report.
- The report: the vulnerability, evidence, impact, likelihood, recommendation; confirmation of the fix by a retest.
- Hands-on training: legal labs and CTF platforms (e.g. TryHackMe, Hack The Box, picoCTF) — never someone else's
  systems.

## The rule for factory agents
An agent **does not run** port and vulnerability scanners, exploit frameworks or password cracking tools against
any system without a written scope and a human's consent in the conversation — also not to "just check" someone else's address. Within the scope
of tests (its own test environment, consent) it applies the rules of engagement above. A passive scan of its own application on
staging (OWASP ZAP in baseline mode) is part of CI (qa-regression, `environment-and-special-data.md`).

## Sources
- RFC 3227 *Guidelines for Evidence Collection and Archiving*; NIST SP 800-86 *Guide to Integrating Forensic Techniques
  into Incident Response*
- [roadmap.sh — Cyber Security](https://roadmap.sh/cyber-security) (forensics, memdump, dd, FTK Imager, Autopsy,
  rules of engagement, blue/red/purple teams, CTF)
Described in our own words.
