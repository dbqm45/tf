---
name: ops-supply-chain-security
description: Use when securing dependencies — lockfiles, release-age cooldown, install scripts, OIDC publishing, audits per ecosystem, SBOM, a compromised package.
metadata:
  review: "2027-05-20"
  catalog: "Use when hardening the dependency supply chain — committed lockfiles and frozen installs, a release-age cooldown (npm min-release-age, pnpm minimumReleaseAge, Yarn npmMinimalAgeGate) with exceptions, install-script allowlists, publishing through OIDC trusted publishing with provenance, internal scoped packages, SBOM, vulnerability audits per ecosystem and their prioritisation, pinning scanners, the response to a compromised package, dependency rules for AI agents (slopsquatting). Not for building the CI pipeline itself (ops-ci-cd), routine version upgrades (ops-dependency-upgrades) or the AppSec programme (sec-appsec-devsecops)."
  keywords: "łańcuch dostaw, bezpieczeństwo zależności, złośliwa paczka, przejęta paczka, skompromitowana paczka, złośliwa wersja, postinstall, skrypty instalacyjne, ignore-scripts, karencja wersji, świeżo opublikowane wersje, minimalny wiek wersji, cooldown, minimumReleaseAge, min-release-age, npmMinimalAgeGate, onlyBuiltDependencies, allowBuilds, lockfile, package-lock, frozen lockfile, npm ci, audyt zależności, audyt podatności, audyt podatności zależności w CI, polecenia audytu, jak czytać wyniki audytu, utonąć w alertach, za dużo alertów, podatności w zależnościach, monorepo Node Python Go Java, npm audit, pip-audit, govulncheck, composer audit, SBOM, CycloneDX, provenance, trusted publishing, publikacja paczki npm, token npm, paczki wewnętrzne, prywatny rejestr, scope npm, .npmrc, slopsquatting, typosquatting, zmyślona paczka, agent dodaje zależność, CISA KEV, supply chain attack, malicious package, compromised dependency, release age, dependency audit, vulnerable dependencies, internal packages, private registry"
---

# Dependency supply chain

Most compromises arrive through a legitimate name: a hijacked maintainer account publishes a new version, its install script runs on
developer machines and CI runners, and steals tokens. The defences below are cheap and layered: if one fails, the next one stops the attack.
Real incidents and what would have stopped each one: `references/cases.md`.

## 1. Installation
- The lockfile is committed. CI installs only from it: `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`,
  `pip install --require-hashes -r requirements.txt` (or `uv sync --locked`), `go mod download` with `go.sum`.
- A human reads the lockfile diff in review. A **new transitive package** in a PR that only bumped a patch version is a warning sign;
  the pipeline can list added packages and fail on unexpected ones.
- Java: pinned versions and checksum verification — Gradle dependency verification (`gradle/verification-metadata.xml`),
  Maven with a failing checksum policy (`--strict-checksums`).
- The analyzer reports a missing lockfile with the text "ops-supply-chain-security (lockfile in git)".

## 2. Cooldown — do not install what was published an hour ago
Malicious versions are usually detected and pulled within hours, so a delay of **1–3 days** removes most of the risk at almost no cost.

| Tool | Setting | Unit / version |
|---|---|---|
| npm | `min-release-age=3` in `.npmrc` | days; npm ≥ 11.10 |
| pnpm | `minimumReleaseAge: 4320` in `pnpm-workspace.yaml`, exceptions in `minimumReleaseAgeExclude` | minutes; pnpm ≥ 10.16, default 1440 since pnpm 11 |
| Yarn Berry | `npmMinimalAgeGate` in `.yarnrc.yml`, exceptions in `npmPreapprovedPackages` | Yarn ≥ 4.10; check the unit in the docs of your version |
| Renovate | `minimumReleaseAge: "3 days"` | separate from the package manager |
| Dependabot | `cooldown: { default-days: 3 }` in `dependabot.yml` | separate from the package manager |

**Exception for an urgent patch** (a critical, exploited vulnerability in an internet-facing dependency): one package in the exclude list,
a review of the package diff (new files, new dependencies, new install scripts) before merge, target within 24 h, a comment with the PR
and the reviewer, and the exception removed when the version is older than the cooldown. Never switch the cooldown off globally.

## 3. Install scripts
- CI: `npm ci --ignore-scripts` (or `ignore-scripts=true` in `.npmrc`), then rebuild only allowlisted packages.
- pnpm 10 runs no dependency scripts by default; the allowlist is `onlyBuiltDependencies` (pnpm 10) or `allowBuilds` (pnpm 11).
  Yarn Berry: `enableScripts: false` plus `dependenciesMeta.<pkg>.built: true` for the exceptions.
- No installers that pipe a download straight into a shell, in pipelines or Dockerfiles; download, verify the checksum or signature, then run.
- Install dependencies in a job that holds no publish or deploy secrets (ops-ci-cd).

## 4. Publishing your own packages
- **Trusted publishing (OIDC)** from CI instead of a stored token; `npm publish --provenance` (automatic with trusted publishing).
  After the switch, **revoke every old publish token** — a forgotten token bypasses OIDC entirely (see `references/cases.md`).
- Provenance proves *where* a package was built, not that the release was authorised. Bind the trusted publisher to one workflow file and a
  protected environment with required approval; publish only from tags in the main repository, never from fork commits;
  alert on `git+`/`github:` dependencies, which bypass the registry.
- Consumers verify: `npm audit signatures` (registry signatures and provenance attestations).
- Maintainer accounts: hardware keys or passkeys for 2FA, granular short-lived tokens, publishing only from CI, and awareness of
  phishing that imitates the registry ("your 2FA must be reset"). Registries change token rules — check the current npm token types and
  lifetimes before designing the flow.

## 5. Inventory and vulnerability audit
- A **CycloneDX SBOM** per released artifact, generated in CI and stored with it (`@cyclonedx/cyclonedx-npm`, `syft <image> -o cyclonedx-json`).
  It answers "where do we run version X" during an incident in minutes.
- Audit per ecosystem — commands and reading the output: `references/dependency-audit.md`.

| Ecosystem | Command |
|---|---|
| npm / pnpm / Yarn | `npm audit --omit=dev`, `pnpm audit`, `yarn npm audit` |
| Python | `pip-audit -r requirements.txt` |
| Go | `govulncheck ./...` (reports only vulnerable code that is actually called) |
| Rust | `cargo audit` |
| PHP | `composer audit` |
| .NET | `dotnet list package --vulnerable --include-transitive` |
| Java, Dart | no built-in audit: OWASP Dependency-Check or `osv-scanner`; without one → **skipped** |

- Report direct and transitive findings separately (a direct one you fix by a bump; a transitive one needs the parent's release or an override).
- A non-zero exit code means "findings present" — it is information for the report, not a crashed step.
- A missing tool or a network error → "**not checked**", never "0 findings". Record the date and the tool version.
- Severity bands from CVSS: critical ≥ 9.0, high ≥ 7.0, medium ≥ 4.0. Priority, though, comes from **reachability** (is the vulnerable
  function called, is the service exposed) and **known exploitation** (the CISA KEV catalog), not from the score alone.
- The audit never runs `npm audit fix --force` or similar on its own: fixes go through a reviewed PR (ops-dependency-upgrades).
- CVE scanning does not find malicious code: add a malicious-package check (`osv-scanner` reports OpenSSF `MAL-` entries).
- Scanners are third-party code too: pin them by version and digest/SHA and run them without secrets.

## 6. Internal packages (libraries, configs, AI artifacts such as prompts or skills)
- An organisation scope mapped to the private registry in the committed `.npmrc`: `@acme:registry=https://npm.pkg.github.com`.
  The mapping also blocks dependency confusion (a public `@acme/…` package can no longer be picked).
- **No token in the committed file.** CI provides it from the environment (`actions/setup-node` with `registry-url`, `NODE_AUTH_TOKEN`);
  developers keep it in their user-level `~/.npmrc`. External build platforms (Vercel, Netlify, a Docker build) need the token supplied
  separately as their own secret.

## 7. A compromised package — the response
Full procedure: `references/dependency-incident.md`. In short:
1. Establish the facts from the advisory: affected versions, the publication window, the added packages, what the payload does.
2. Search lockfiles and SBOMs of all repositories and release branches with `grep` (do not read whole files). The presence of the malicious
   package's directory in `node_modules` means the install script **has run**.
3. List the machines and runners that installed during the window.
4. **Preserve evidence first** (process list, network connections, the file tree), then **rebuild** the machine or runner — do not "clean" it.
5. **Rotate everything reachable**: registry, GitHub, SSH, cloud keys, `.env` values, browser sessions; then read the access logs for use
   of the old credentials.
6. Pin a safe version (`overrides` / `resolutions`), clear the package cache, reinstall with scripts disabled.
7. Post-mortem: which safeguard from sections 1–4 would have stopped it, and add it. Never "just run `npm update`".

## 8. Rules for AI agents adding dependencies
- No new dependency without a human's explicit consent; propose it with the reason and the alternative of no dependency.
- Models invent plausible package names, and attackers register them (**slopsquatting**). Before proposing a package verify: it exists
  under exactly that name, the publisher and repository, the last release date and history, provenance, download count, and how many
  transitive packages it brings. An unverifiable name is not proposed.
- Optional CI rule: fail on a dependency younger than the cooldown or with very few downloads unless it is on an approved list.
- Agent hooks may ask before `npm install <pkg>` (core-agent-security).

## Example
Request: "Set pnpm and npm so we never install freshly published versions."

Result:
```yaml
# pnpm-workspace.yaml (pnpm ≥ 10.16)
minimumReleaseAge: 4320            # minutes = 3 days
minimumReleaseAgeExclude: []       # urgent patches only, with a diff review; remove after 3 days
onlyBuiltDependencies: [esbuild]   # pnpm 10; in pnpm 11 use allowBuilds
```
```ini
# .npmrc (npm ≥ 11.10)
min-release-age=3                  # days
ignore-scripts=true
```
Plus: "Renovate gets its own `minimumReleaseAge: \"3 days\"`. CI installs with `--frozen-lockfile` / `npm ci`. Malicious versions are
usually pulled within hours, so three days removes most of the risk."

More in `references/examples.md`: 1. "did the compromised axios hit us?" across many repositories · 2. a cooldown and a script
allowlist in pnpm · 3. publishing your own package through OIDC.

## Related skills
ops-ci-cd · ops-docker · ops-secrets-identities (rotation) · ops-dependency-upgrades · eng-repo-readiness (the dependency audit
after the skeleton) · core-project-record · core-agent-security · be-auth-security.

## Sources
- npm Docs: `npm ci`, `npm audit`, `npm audit signatures`, config `min-release-age` and `ignore-scripts`, "Trusted publishing for npm
  packages", "Generating provenance statements" (docs.npmjs.com), as of 2026-11.
- pnpm documentation: settings `minimumReleaseAge`, `minimumReleaseAgeExclude`, `onlyBuiltDependencies`, `allowBuilds` (pnpm.io), as of 2026-11.
- Yarn documentation: `.yarnrc.yml` settings `npmMinimalAgeGate`, `npmPreapprovedPackages`, `enableScripts` (yarnpkg.com), as of 2026-11.
- Renovate docs `minimumReleaseAge` (docs.renovatebot.com); GitHub Docs, Dependabot options `cooldown` (docs.github.com), as of 2026-11.
- pip-audit (github.com/pypa/pip-audit); govulncheck (pkg.go.dev/golang.org/x/vuln/cmd/govulncheck); Composer docs, the `audit`
  command (getcomposer.org/doc/03-cli.md); `dotnet list package` (learn.microsoft.com); cargo-audit (rustsec.org); OWASP
  Dependency-Check; osv-scanner (google.github.io/osv-scanner), as of 2026-11.
- Gradle "Verifying dependencies" (docs.gradle.org); Maven `--strict-checksums` (maven.apache.org), as of 2026-11.
- CycloneDX specification (cyclonedx.org); FIRST CVSS v3.1/v4.0 severity ratings (first.org); CISA Known Exploited Vulnerabilities
  catalog (cisa.gov), as of 2026-11.
