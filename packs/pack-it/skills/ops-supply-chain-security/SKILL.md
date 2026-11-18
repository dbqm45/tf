---
name: ops-supply-chain-security
description: Use for the dependency supply chain — lockfile, version cooldown, install scripts, SBOM, taken-over packages.
metadata:
  review: "2027-04-10"
  catalog: "Use when adding and updating dependencies, reviewing a lockfile, configuring a package manager, publishing packages and for the question \"did a compromised package hit us\" — lockfile and npm ci, a cooldown for new versions, install scripts, provenance, publishing tokens, SBOM, a fast track for patches, the post-incident procedure. Not for the pipeline itself (ops-ci-cd) or application auth (be-auth-security)."
  keywords: "audyt zależności, audyt podatności zależności, podatności w zależnościach, npm audit, pip-audit, govulncheck, cargo audit, composer audit, CVE w paczkach, lockfile, nowa zależność, przejęta paczka, skompromitowana paczka, typosquatting, slopsquatting, SBOM, paczka wewnętrzna, prywatny rejestr npm, dependency audit, dependency vulnerability audit, vulnerabilities in dependencies, CVE in packages, new dependency, taken-over package, compromised package, internal package, private npm registry"
---

# Software supply chain security

A dependency has the same permissions as your code: at install time it runs on the developer's laptop and on the
CI runner, where npm tokens, SSH keys, cloud credentials and `.env` files are stored. The axios case (March 2026):
a taken-over maintainer account, a new dependency with a `postinstall` hook, the first infected machines after 89 seconds, the malicious
versions available for about 3 hours. Details and other cases: `references/cases.md`.

## 1. Reproducible installation
- A lockfile in the repository; in CI only `npm ci` / `pnpm install --frozen-lockfile` / `yarn install --immutable`.
- A human reads the lockfile diff in the PR. **A new transitive dependency** that was not there before is a red flag
  (in axios it was `plain-crypto-js`) — the pipeline can detect it and require approval.
- Java: pinned versions (no ranges and no `LATEST`), checksum verification (Gradle `verification-metadata.xml`,
  Maven with `checksumPolicy=fail`); build plugins are also code that runs on your side.

## 2. A cooldown for new versions
Malicious versions usually disappear from the registry within hours, so install versions older than 1–3 days.

| Manager | Setting | Unit | Since version |
|---|---|---|---|
| npm | `min-release-age=3` in `.npmrc` | days | npm 11.10 |
| pnpm | `minimumReleaseAge: 4320` in `pnpm-workspace.yaml`, exceptions `minimumReleaseAgeExclude` | minutes | pnpm 10.16 (from 11 the default is 1440) |
| Yarn Berry | `npmMinimalAgeGate: 4320` in `.yarnrc.yml`, exceptions `npmPreapprovedPackages` | minutes | Yarn 4.10 |

Renovate and Dependabot have their own delay settings — configure them separately.

**The exception: security patches.** A critical vulnerability in an internet-facing component (React2Shell: disclosed
on 3 December 2025, attacks from 4 December) requires deployment within 24 hours. You let the patch through deliberately via the exception list,
with a review of the package diff, not by disabling the cooldown for everything.

## 3. Install scripts
- In CI `--ignore-scripts` as a rule. Packages that really need a script (native binaries, e.g. esbuild)
  are allowed from an allowlist: pnpm `onlyBuiltDependencies` (pnpm 10) or `allowBuilds` (pnpm 11), npm with `@lavamoat/allow-scripts`.
- Never `curl … | sh` or `iwr … | iex` as an installation step in the repository or CI — download, check the checksum, only then run. <!-- audit-ok: a description of an attack, not a command -->

## 4. Publishing your own packages
- **Trusted publishing (OIDC) and the removal of classic npm tokens.** In axios OIDC was configured, but a long-lived
  token still worked, and the malicious versions were published with it.
- Publish from CI with `--provenance`; consumers check `npm audit signatures`.
- **Provenance tells you where the package was built, not whether the build was authorized.** In the Mini Shai-Hulud campaign (2026)
  the attackers used the victims' own workflows and their OIDC tokens (an orphaned commit via a fork bypassed branch protection),
  so the malicious versions had valid provenance. Therefore: a trusted publisher pinned to a specific workflow file
  and a protected environment with required approval; publishing never from commits from forks; an alarm on dependencies fetched
  straight from GitHub (`github:…`, a git URL), especially optional ones.
- Maintainer accounts: hardware keys or passkeys (WebAuthn) instead of TOTP codes; local publishing tokens only
  granular and short-lived (npm shortens their default validity to 7 days), classic ones removed.
- **Internal packages** (also AI artifacts: skills, rules, prompts distributed as a package): the organization scope
  mapped to the private registry in the repository's `.npmrc` (without a token) — this also protects against a name substitution by a package
  from the public npm; the read token only from a CI environment variable. External build platforms do not see
  GitHub secrets — you sync the token separately to their secret store (production and preview). The kind of token for
  reading GitHub Packages changes from time to time (classic tokens are being phased out) — check the current documentation before rollout.
- A person with publishing rights is a target of social engineering: the axios maintainer was persuaded during a fake meeting
  (a forged Slack and Teams) to install a "fix". Publishing rights only in CI, not on a laptop; no installation
  of software at the request of the other party in a conversation.

## 5. Knowing what you have
- An SBOM (CycloneDX) generated in CI for every artifact — the answer to "do we have version X?" in minutes, not days.
- **An audit of known vulnerabilities** in CI and at the start of work in a repo — commands for npm, pnpm, Python, Rust, Go, Ruby,
  PHP and .NET, CVSS thresholds and reading the results: `references/dependency-audit.md`. You report direct dependencies
  separately from transitive ones; an ecosystem without a built-in audit (Java, Dart) is "skipped", never "0 findings"; the audit
  does not fix anything by itself (`npm audit fix` only with consent, with a review of the lockfile diff).
- Security tools in CI (scanners, linters) are also the supply chain: in the TeamPCP campaign Trivy was swapped through
  GitHub Actions. Pin them like any action (SHA, image digest) — ops-ci-cd.
- A dependency scan with malicious code detection (not only known CVEs) in the pipeline.
- **Scanners without secrets:** the job with the scanner has no write tokens or cloud credentials — the swapped Trivy read
  secrets from the runner process memory and then performed a normal scan, so that nobody noticed anything. You pin the versions of build
  tools the same way as the application's dependencies.
- **Vulnerability priorities:** first what is reachable (package → artifact → image → internet-facing service)
  and known to be exploited in attacks (e.g. the CISA KEV catalog); a reachability finding has an indicated evidence path.
  An AI model may explain a finding, but it does not decide whether a vulnerability is exploitable.

## 6. After a package compromise is reported
The step-by-step procedure: `references/dependency-incident.md`. In short: find the version in the lockfiles and in `node_modules`,
check for traces on the machines that installed during the attack window, **rebuild** the infected machines instead of "cleaning" them,
rotate every secret reachable from those machines and runners, pin a safe version (`overrides` / `resolutions`).

## The agent and dependencies
- The agent does not add a new dependency without a human's consent (the guard_bash hook asks on `npm install <package>`) and does not raise
  versions in an existing project on its own initiative.
- **Slopsquatting:** AI models invent package names that do not exist, and they do it repeatably, so attackers
  can register those names. You check a package proposed by AI in the registry and the documentation before it enters the project;
  CI can block new dependencies younger than N days or with a very small number of downloads.
- Before proposing a new package: the name exactly the same as in the project's documentation (typosquatting), the publisher, the date of the latest
  version, provenance, the number of transitive dependencies. Fewer dependencies means a smaller attack surface.

## Example
**Situation:** "I heard about the taken-over axios. We have 12 repositories in Node — are we affected?"
**Result:** an answer based on `grep`, not on reading the lockfiles:
- `grep -rn 'plain-crypto-js'` in `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` of all repositories and release
  branches, plus axios versions 1.14.1 and 0.30.4.
- The `node_modules/plain-crypto-js` directory on a runner or a laptop = `postinstall` was executed → the machine is compromised.
- A hit: rebuilding the machines that installed during the attack window, rotating the secrets from them, `overrides` with a safe version.
- No hits: an entry in the log and a conclusion on what would have stopped the attack (a cooldown, blocking scripts, an alarm on a new package).

More examples: `references/examples.md`.

## Checklist
- [ ] a lockfile in the repo, a "frozen" installation in CI, the lockfile diff reviewed (new transitive packages?)
- [ ] a cooldown for new versions in the package manager and in Renovate/Dependabot; an exception path for patches
- [ ] install scripts disabled in CI or from an allowlist
- [ ] publishing through OIDC with provenance, classic tokens revoked
- [ ] an SBOM in CI, a malicious code scan, tool actions and images pinned
- [ ] a vulnerability audit for every ecosystem in the repo (direct separately from transitive, "skipped" instead of "0")
- [ ] the "did it hit us" procedure known to the team

## Sources
- The 10xDevs course, ed. 3 (2026), module 1 (verification after setting up the skeleton, the dependency audit) and module 5, lesson 4
  (distributing internal packages in a team) — training material (accessed 2026-10-09); described in our own words.
- `pip-audit --help` (2.10.1, checked 2026-10-10); Composer 2.4 and `composer audit` —
  [php.watch](https://php.watch/articles/composer-audit); govulncheck —
  [pkg.go.dev](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck); `dotnet list package` —
  [learn.microsoft.com](https://learn.microsoft.com/dotnet/core/tools/dotnet-list-package) (accessed 2026-10-10).
