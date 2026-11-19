---
name: ops-dependency-upgrades
description: Use when a human asks to upgrade dependencies — inventory, order, codemods, Renovate/Dependabot.
metadata:
  review: "2027-04-17"
  catalog: "Use when a human asks to upgrade dependencies, a framework or a runtime, or to set up regular updates — an inventory of outdated versions and end of support, priorities, minor updates in batches and major ones individually, one major at a time with a migration guide, codemods (ng update, @next/codemod, React codemod, OpenRewrite, ruff UP), tests as a safety net, Renovate and Dependabot configuration (groups, schedule, automerge, PR limit) and rollback. Not for supply chain security — the cooldown, compromised packages, provenance (ops-supply-chain-security) — or for aligning skills with the project's versions without changing dependencies (core-stack-sync)."
  keywords: "aktualizacja zależności, podnieść zależności, upgrade zależności, Renovate, Dependabot, ncu, uv lock --upgrade, OpenRewrite, codemod, koniec wsparcia, EOL, nieaktualne zależności, dependency update, upgrade dependencies, dependency upgrade, end of support, outdated dependencies"
---

# Planned dependency upgrades

**You upgrade dependencies only at a human's request** (a factory rule). The agent prepares a plan, carries it out in a branch
and shows the evidence; a human approves the merge and the deployment. Package security (the cooldown for new versions,
taken-over packages, provenance) is in ops-supply-chain-security and applies here as well.

## Procedure
1. **Inventory:**
   - what is outdated (the commands below);
   - what **reaches end of support** — the runtime, the framework, the database; you check it in the official release
     schedule, with a date;
   - which versions have known vulnerabilities (ops-supply-chain-security).
2. **Priorities:**
   1. a patch for a critical vulnerability in an externally exposed component — the fast track;
   2. end of support in the coming months;
   3. an update blocking other work;
   4. the rest regularly, in small portions.
   Update debt grows non-linearly: a jump of three major versions costs more than three separate jumps.
3. **A safety net before the change:**
   - a green test suite, build, lint and type checking on the current versions — record the result and the number of warnings
     about deprecated APIs;
   - weak coverage of the critical paths → characterization tests first (eng-behavior-preserving-refactoring).
4. **Minor ones (patch, minor):**
   - in batches and regularly, e.g. one group once a week;
   - after the update, the full test suite;
   - automatic merging only with a green CI, with a cooldown and with a human's consent to this rule.
5. **Major ones — individually, one major version at a time:**
   - first the latest version of the **current** line, which often warns about what will disappear (e.g. React 18.3 before 19);
   - read the release notes and the migration guide of **every** version on the way;
   - you check the prerequisites separately: Spring Boot 3 requires Java 17+ and the `jakarta.*` namespace,
     Next.js 16 — Node ≥20.9 and React 19;
   - the order: the runtime (Node, JDK, Python) → the framework → libraries dependent on the framework → the rest;
   - you update Angular with `ng update` one major version at a time.
6. **Codemods instead of manual changes**, then a review of the diff:

   | Technology | Tool |
   |---|---|
   | Angular | `ng update @angular/core@<N> @angular/cli@<N>` (angular.dev/update-guide); in Nx `nx migrate` |
   | Next.js | `npx @next/codemod upgrade major` (or `minor`, `patch`, a version); single transforms, e.g. `next-async-request-api` |
   | React | `npx codemod@latest react/19/migration-recipe`, types: `npx types-react-codemod@latest preset-19 ./src` |
   | Java, Spring | OpenRewrite: `rewrite-maven-plugin` with the recipes `org.openrewrite.java.migrate.UpgradeToJava21`, `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_5` (first `rewrite:dryRun`) |
   | Python | `ruff check --select UP --fix` (syntax compatible with `requires-python`) |

7. **Small steps in a branch:**
   - separate commits: the version bump and the lockfile → the codemod result → manual fixes;
   - build and tests after every step;
   - the PR lists the breaking changes, the test results before and after, and what was not checked.
8. **Rollback:**
   - before the merge, a known way back: revert the PR, the previous lockfile, the previous image;
   - for a large jump (framework, runtime, database) a gradual release with observation (ops-release-engineering);
   - an irreversible data migration → a separate decision by a human.
9. **After the update:**
   - `detect_stack.py` will show whether the factory's skills describe the new version (`SKILL_OUTDATED` → core-stack-sync);
   - a library published further whose minimum runtime version was raised → a MAJOR bump (core-semver).

## Commands — what is outdated and how to upgrade
| Ecosystem | List of outdated | Update |
|---|---|---|
| npm | `npm outdated` | `npm update` (within the ranges from `package.json`); beyond the range: `npx npm-check-updates -u --target minor` or `latest`, then `npm install` |
| pnpm | `pnpm outdated -r` | `pnpm up -r`, beyond the range: `pnpm up --latest --interactive` |
| uv | `uv tree --outdated` | one package: `uv lock --upgrade-package <name>`, everything: `uv lock --upgrade`; then `uv sync` |
| pip | `pip list --outdated` | a change in the requirements file and a reinstall in a clean environment |
| Maven | `mvn versions:display-dependency-updates`, `…:display-plugin-updates` | a version change in `pom.xml` (or `versions:use-latest-releases` with a review of the diff) |
| Gradle | the `com.github.ben-manes.versions` plugin: `./gradlew dependencyUpdates` | a change in the version catalog (`libs.versions.toml`) |

## Automation: Renovate and Dependabot
- **Groups:** minor updates together (e.g. all development patch and minor ones in one PR), major ones separately.
- **Schedule:** a window once a week, not a stream of PRs all day.
- **Limit of open PRs:** the team keeps up with the review.
- **Cooldown for new versions:** Renovate `minimumReleaseAge`, Dependabot `cooldown` (on github.com Dependabot has
  a 3-day cooldown for version updates by default); security patches go without a cooldown, through the exception path.
- **Automatic merging:** only patch/minor, only with a green CI, never for major.
- **Lockfile maintenance** (Renovate `lockFileMaintenance`): a periodic refresh of transitive dependencies.
- Sample, verified configurations: `references/configurations.md`.

## Checklist
- [ ] a human's request for the update; an inventory with end-of-support dates from a source
- [ ] the "before" state: tests, build, types, the number of warnings about deprecated APIs
- [ ] one major version at a time; the migration guide of every version read; codemods before manual changes
- [ ] separate commits: versions → codemod → fixes; tests after every step
- [ ] a PR with the breaking changes, the result before and after, and a rollback plan
- [ ] a cooldown and an exception path for security patches (ops-supply-chain-security)

## Sources
- docs.renovatebot.com (configuration-options, presets) — Renovate 44, the configuration checked with `renovate-config-validator`
- docs.github.com: Dependabot options reference (`groups`, `cooldown`, `schedule`, the `uv` ecosystem)
- docs.npmjs.com (`npm update`, `npm outdated`), pnpm.io (`pnpm update`, `pnpm outdated`), uv CLI 0.12 (`uv lock --upgrade-package`, `uv tree --outdated`)
- angular.dev/update-guide and /reference/releases; nextjs.org/docs (codemods); react.dev (React 19 Upgrade Guide);
  docs.openrewrite.org (rewrite-migrate-java, rewrite-spring); nodejs.org — the release schedule (github.com/nodejs/Release)
Accessed 2026-10-03. Described in our own words.
