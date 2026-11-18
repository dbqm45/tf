---
name: sec-appsec-devsecops
description: Use for an application security program in the pipeline — ASVS, SAMM, SAST, DAST, SCA, vulnerability triage and SLAs, SLSA, signatures, metrics.
metadata:
  review: "2027-04-17"
  catalog: "Use when you build or assess an application security program in the delivery cycle (AppSec, DevSecOps) — requirements per OWASP ASVS 5.0 and maturity per OWASP SAMM and DSOMM, mapping onto NIST SSDF (SP 800-218), shift left and secure defaults, security code review (dangerous APIs and default configurations per language), scanner layers in CI/CD (secrets, SAST, SCA and SBOM, DAST, IAST, IaC and containers) and the place of each, tuning false positives, triage and fix deadlines per CVSS v4, EPSS and CISA KEV, the build-blocking policy, chain integrity (SLSA, provenance, Sigstore/cosign), security champions, metrics (MTTR, coverage). Not for pipeline mechanics (ops-ci-cd), lockfiles and dependency cooldowns (ops-supply-chain-security), the threat model (arch-threat-modeling), auth code (be-auth-security), patches and incidents in operations (ops-security-operations), secrets (ops-secrets-identities) or searching for variants of a found vulnerability (sec-variant-analysis)."
  keywords: "SSDF, NIST SP 800-218, DSOMM, DevSecOps Maturity Model, shift left, secure by default, bezpieczne ustawienia domyślne, zgodność z SSDF, devsecops, appsec, bezpieczeństwo aplikacji, ASVS, SAMM, SAST, DAST, IAST, SCA, semgrep, codeql, zap, trivy, grype, syft, dependency-track, SBOM cyclonedx spdx, skaner w CI, fałszywe alarmy, false positives, blokować build, SLA podatności, CVSS, EPSS, KEV, MTTR podatności, SLSA, cosign, sigstore, provenance, security champions, podpisywanie obrazów, podpis obrazu kontenera, nikt go nie podmienił, zbudowano w naszym CI, integralność artefaktu, przegląd kodu security, pentest, wymagania bezpieczeństwa, niebezpieczne funkcje, niebezpieczne API, domyślne ustawienia, domyślne hasła, tryb debug na produkcji, wyłączona weryfikacja certyfikatu, pickle, yaml.load, BinaryFormatter, InsecureSkipVerify, przegląd bezpieczeństwa przed wydaniem, secure defaults, SSDF compliance, application security, scanner in CI, block the build, vulnerability SLA, vulnerability MTTR, image signing, container image signature, nobody swapped it, built in our CI, artifact integrity, security code review, security requirements, dangerous functions, dangerous APIs, default settings, default passwords, debug mode in production, disabled certificate verification, security review before release"
---

# AppSec in the pipeline (DevSecOps)

Goal: find a vulnerability where it is cheapest to fix (shift left), start from secure
defaults and not flood the team with noise. The program consists of four
things: **requirements** (what must be secure), **controls in the pipeline** (what the machine checks), **human review**
(what requires judgement) and **measurement** (whether it works). Boundaries: job mechanics and runner permissions are `ops-ci-cd`,
lockfiles and cooldowns are `ops-supply-chain-security`, STRIDE is `arch-threat-modeling`, patching in production
is `ops-security-operations`.

## Procedure
1. **Baseline.** What already scans (repo, CI, cloud), who reacts to the results, how many open findings there are and how
   old. Without this there is no reference point for the metrics.
2. **Requirements.** Choose the ASVS level for the application (L1 every one, L2 by default for sensitive data, L3 critical)
   and record the chosen chapters as acceptance criteria. The maturity of the whole program (not one application) is assessed by SAMM,
   the maturity of the pipeline by DSOMM; a NIST SSDF compliance requirement is a table practice → control → evidence from the pipeline.
   Details and versions: `references/standards-and-metrics.md`.
3. **Control layers** (table below): for each, state the stage, the tool, the mode (blocks / warns) and the owner.
   Start with those with the best signal-to-noise ratio: secrets, SCA, SAST with a small rule set.
4. **Tuning before blocking.** A new tool runs for 2–4 weeks in warning mode; measure the share of
   findings judged true, disable low-precision rules, add your own rules for company patterns.
   Exceptions (suppress) have a reason, an owner and an expiry date, not an "ignore" entry in the code without a trace.
5. **Triage and deadlines.** Priority rules and an example SLA table: `references/triage-and-sla.md`. In short: base severity
   (CVSS), plus known exploitation (CISA KEV), probability (EPSS), reachability in code and service exposure.
6. **Blocking policy.** Block only what has high precision and a clear fix: an exposed secret, a known
   exploited vulnerability in a reachable dependency, a critical SAST finding new in the diff. Report the rest as
   a task with a deadline. Scan the **diff** in the PR (new debt), and everything at night (old debt). Disabling a gate is a
   human decision with an entry in the exception register.
7. **Artifact integrity.** Every released artifact has an SBOM, provenance and a signature; the deployment verifies the signature
   and the builder's identity (section below).
8. **People.** A security champion in the team (about 1 per team, part-time, supported by training and a channel to AppSec),
   a security review for changes in auth, cryptography, input parsing, uploads and new integrations.
9. **Measurement** every month: MTTR by severity, the share of findings past the deadline, coverage (repositories with a scanner / all),
   the false positive rate, the number of vulnerabilities found after deployment (escapes). The metrics serve to improve the
   process, not to rank teams.

## Control layers
| Layer | Examples | Where | Default mode |
|---|---|---|---|
| Secrets | gitleaks, trufflehog, push protection | pre-commit + CI + history | blocks |
| SAST | Semgrep, CodeQL | PR (diff) + nightly (everything) | blocks new critical, warns on the rest |
| SCA + SBOM | Grype, osv-scanner, Syft, CycloneDX/SPDX, Dependency-Track | PR + build + continuously after release | blocks known exploited |
| IaC | Checkov, KICS, tfsec/Trivy | PR | warns, blocks public storage and open ports |
| Container | Trivy, Grype on the image | build + registry | blocks critical with a fix |
| DAST | OWASP ZAP | staging, nightly, after deployment | warns (agreed scope) |
| IAST | an agent in tests | integration tests | warns |
Offensive tests only on your own environments and with consent. Scanners are also external code: you pin them
and isolate them from secrets (`ops-ci-cd`, `ops-supply-chain-security`).

## Security code review
Scanners do not see logic. A human (or an agent, with a human approving the result) checks: access control on every
resource (IDOR), validation at the boundary, building queries and commands from input, deserialization, SSRF when fetching URLs,
error handling without leaks, logs without sensitive data. A list of questions per ASVS, not per intuition.
Dangerous APIs per language (Python, JS/Node, Java, C#, Go) and default configurations (accounts, debug, TLS, CORS,
services without authentication, fail-open): `references/dangerous-apis.md`. After finding a vulnerability — its
variants in the rest of the code and a rule in CI: sec-variant-analysis.

## The artifact supply chain
- **SLSA** (build track, v1.0): L1 provenance exists, L2 provenance is signed by a hosted build platform, L3 the platform
  is hardened (isolated, ephemeral builds, the key inaccessible to the steps). Aim for L2, for L3 for critical releases.
- **A signature** without a long-lived key: Sigstore/cosign in keyless mode (OIDC identity from CI, a short-lived certificate,
  an entry in the transparency log). Verification at deployment checks **the identity and the issuer**, not just that a signature exists.
- Provenance says how it was built; the SBOM, from what; the signature, by whom. None of them proves the absence of vulnerabilities.

## Example
**Situation:** "We have Semgrep in CI, 900 findings, nobody reads them. What do we do?"
**Result** [example]: (1) week 1: Semgrep only on the PR diff, the rule set limited to security categories
with high confidence, the rest nightly without blocking; (2) a sample of 50 findings → 14 true (28%), 3 rules
responsible for 60% of the false ones disabled; (3) blocking only for new "high" findings with "high" confidence; (4) old ones get
tasks with a deadline per the SLA table, the 20 most important per sprint; (5) we measure MTTR and the false positive rate every month.

## Checklist
- [ ] ASVS level chosen and recorded as criteria, program maturity assessed (SAMM)
- [ ] every layer has a stage, a mode, an owner; new tools first in warning mode
- [ ] priority from CVSS + KEV + EPSS + reachability; deadlines per severity; exceptions with an expiry date
- [ ] blocking only for high-precision findings; diff scan in the PR
- [ ] SBOM, provenance and signature; verification at deployment
- [ ] security champions and metrics (MTTR, coverage, false positives)

## Sources
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) — version 5.0.0, 30.05.2025 (search 17.10.2026)
- [OWASP SAMM](https://owaspsamm.org/), [SLSA v1.0](https://slsa.dev/spec/v1.0/levels), [Sigstore](https://docs.sigstore.dev/signing/overview/) (17.10.2026)
- NIST SP 800-218 SSDF 1.1 (final, 02.2022; 1.2 — draft 12.2025); [OWASP DSOMM](https://dsomm.owasp.org/)
  (version [unverified]); statuses per search 2026-10-27
- FIRST: CVSS v4.0 (November 2023), EPSS; [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
Described in our own words. Details and markers of unverified facts: the files in `references/`.
