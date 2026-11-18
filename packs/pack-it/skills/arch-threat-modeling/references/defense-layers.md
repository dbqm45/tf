# Layers of defence (defence in depth) — a map for the review

The principle: every control will fail at some point, so another one stands behind it. The review goes through the layers one by one and for each
asks about three kinds of controls: **preventive** (blocks), **detective** (notices) and **corrective** (restores).
A layer without a control is a hole or a conscious decision — then record the risk acceptance with an owner and a review date
(procedure step 5).

| Layer | Typical controls | Review question | Skill |
|---|---|---|---|
| network | segmentation and microsegmentation, traffic filtering (deny by default), WAF, DDoS protection, restricted egress | How far will an attacker get after taking over one service (blast radius)? | sec-zero-trust-identity, ops-security-operations (network and cloud), ops-kubernetes (NetworkPolicy), ops-cloud-landing-zones |
| identity and access | phishing-resistant MFA, least privilege, short-lived credentials, PAM and JIT, machine identities | Who can do what with this resource, and how do we know? | be-auth-security, sec-zero-trust-identity, ops-secrets-identities |
| host and runtime | hardening (a CIS baseline), patches, inventory, EDR, a container without root | Does every host and image have a baseline and checked drift? | ops-security-operations (host hardening), ops-docker, sec-cloud-security |
| application | secure design (this skill), input validation, per-object authorization, SAST/DAST/SCA, secure defaults | Which flows across a trust boundary have no control and no abuse case test? | sec-appsec-devsecops, be-auth-security, fe-web-platform, sec-llm-security |
| data | data classes, encryption in transit and at rest, control of access to keys, backups, lifecycle and deletion | What will leak when an attacker gets a copy of the database or the application's access? | sec-cryptography-pki (data at rest), arch-privacy-compliance, ops-sre-incidents (backups) |
| supply chain | lockfile, a version cooldown, SBOM, signatures and provenance, CI permissions | Do we know what we deploy and who built it? | ops-supply-chain-security, sec-appsec-devsecops (SLSA), ops-ci-cd |
| monitoring and detection | central security logs, detection rules with a test, SIEM, EDR, IDS | How long until we notice abuse from this path and who gets the alarm? | ops-security-operations, sec-detection-engineering, ops-observability |
| response and recovery | a response plan, playbooks and runbooks, exercises, backups with a restore test | Who does what in the first hour and how much data will we lose? | ops-security-operations (NIST SP 800-61r3), ops-sre-incidents, sec-security-leadership (tabletop) |

## How to use it in the threat model
1. After STRIDE (procedure step 4) assign every threat to the layers that can stop it, detect it and fix it.
2. A threat stopped by **one** control in **one** layer is a candidate for an additional control —
   especially for high-value assets.
3. In `threat-model.md` add a short table: layer → controls present → gaps → decision. The details of the controls are described by
   the skills from the "Skill" column; this file only makes sure no layer is skipped.
