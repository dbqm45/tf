---
name: ops-secrets-identities
description: Use for secrets and machine identities — scanning, rotation, OIDC instead of keys, PKI.
metadata:
  review: "2027-04-17"
  catalog: "Use for secrets and machine identities — an inventory of service accounts, tokens, keys and certificates (owner, scope, expiry), separating the build and deployment identities, secret scanning before commit and in CI, push protection, rotation and clean-up, a cryptography inventory (CBOM). Not for authenticating application users (be-auth-security) or dependencies (ops-supply-chain-security)."
---

# Secrets and machine identities

Non-human identities (service accounts, CI tokens, deploy keys, cloud roles, GitHub apps, AI agent tokens)
multiply faster than human accounts and do not go through HR processes: nobody "lets them go". Access granted in an emergency
stays for years. A leaked secret pushed to a public repository can be exploited within minutes.

## 1. Inventory
For every identity that reaches production or the repositories: **the owner, the purpose, the scope of permissions, the creation
date, the expiry date, the last use, what depends on it.**
- GitHub Enterprise Cloud provides a credential inventory (SSH keys, classic and fine-grained PATs, OAuth app
  and GitHub App tokens) as CSV and through the REST API, with a separate permission for viewing only. Fetch it daily
  and alert on tokens with no expiry date, with too broad a scope and unused for 90 days.
- The inventory only reports — clean-up and bans (e.g. a maximum PAT lifetime) you configure separately.
- Treat AI agent tokens as a priority: they have broad permissions and act without supervision (core-agent-security).

## 2. Least privilege and a short lifetime
- **Build and deployment are separate identities.** The build job has no deployment roles and no access to production.
- Credentials issued on demand (OIDC → a cloud role, Vault with dynamic secrets), valid for minutes or hours,
  instead of static keys in CI secrets.
- A periodic review: who assumes which cloud roles, which integrations the repository has; remove unused permissions
  (e.g. AWS IAM Access Analyzer shows unused actions).

## 3. Secret scanning in three places
1. **Before commit** (on the developer's machine): Gitleaks or TruffleHog on the files added to the index (`--staged`),
   in under about 5 s — people bypass a slow hook. Before push, heavier scans (OSV-Scanner, Semgrep, Trivy).
2. **On push:** GitHub push protection (on by default in public repositories for selected token types;
   in private ones it has to be turned on — GitHub Secret Protection) with a validity check —
   you deal first with the secrets that still work.
3. **In CI** as the final safeguard, because local hooks can be skipped (`--no-verify`).
Every exception to the scanner has an owner, a justification and an expiry date. Code written by AI goes through the same scans
as human code — vendor reports indicate that repositories written with AI assistants have more secret leaks.

## 4. When a secret leaks
- You rotate immediately (revoke, issue a new one), and only then clean the history. Removing it from the file closes nothing.
- After an incident you revoke **all** credentials reachable from the compromised place: in the campaign around Trivy
  the attackers came back because the first breach was not closed (according to CloudSEK's analysis — through one unrevoked
  token). You assume that stolen credentials can be used long after the incident.

## 5. Keys, certificates and cryptography
- Certificates with automatic renewal and an alert on approaching expiry.
- Choosing algorithms, KMS and envelope encryption, the certificate lifecycle, your own PKI with failure resilience,
  post-quantum cryptography: `references/cryptography-and-pki.md`.
- A cryptography inventory (CBOM, CycloneDX format): which algorithms, libraries, protocols, certificates and keys
  each application uses and how sensitive the data they protect is. It is the first step before migrating to algorithms resistant to quantum
  computers; data that is sensitive and stored for a long time has priority.

## Example
**Situation:** an AWS key from `deploy.env` reached a public repository; the file was removed in the next commit.
**Result:** a runbook — rotation before clean-up:
1. 15 min: deactivate the key of the `svc-shop-deploy` account (owner and dependencies from the inventory).
2. 1 h: a new credential or straight away a role through OIDC pinned to `repo:acme/shop:environment:production`.
3. 4 h: the cloud audit logs from the window between the push and the deactivation.
4. 24 h: rotation of everything reachable from that role (the database password, the payment token).
5. 2 days: history clean-up, push protection, a `--staged` scan in the hook; the old key deleted.

More examples: `references/examples.md`.

## Checklist
- [ ] every machine identity has an owner, a scope and an expiry date; no tokens that never expire
- [ ] build and deployment on separate identities; short-lived credentials through OIDC
- [ ] secret scanning before commit, push protection and a scan in CI; exceptions with an expiry date
- [ ] the rotation procedure known and rehearsed; after an incident, rotation of everything reachable

## Sources (devops.com)
- [Your CI/CD Pipeline Has Non-Human Identities You Forgot About](https://devops.com/your-ci-cd-pipeline-has-non-human-identities-you-forgot-about/)
- [GitHub Gives Enterprises a Full Count of Who Holds the Keys](https://devops.com/github-gives-enterprises-a-full-count-of-who-holds-the-keys/)
- [Shift Left to the Developer's Machine: Local Git Security Gates](https://devops.com/shift-left-to-the-developers-machine-building-local-git-security-gates/)
- [GitHub Adds 37 New Secret Detectors, Extends Scanning to AI Coding Agents](https://devops.com/github-adds-37-new-secret-detectors-in-march-extends-scanning-to-ai-coding-agents/)
- [Secrets Management Failures in CI/CD Pipelines](https://devops.com/secrets-management-failures-in-ci-cd-pipelines/)
- [Sophisticated Supply Chain Attack Targeting Trivy Expands to Checkmarx, LiteLLM](https://devops.com/sophisticated-supply-chain-attack-targeting-trivy-expands-to-checkmarx-litellm/)
- [LiteLLM Attack Affected 2,500 Companies, 434,000 CI/CD Pipelines](https://devops.com/litellm-attack-affected-2500-companies-434000-ci-cd-pipelines-cloudsek/)
- [Why Cryptographic Inventory Is the First Step Toward Quantum Readiness](https://devops.com/why-cryptographic-inventory-is-the-first-step-toward-quantum-readiness/)
